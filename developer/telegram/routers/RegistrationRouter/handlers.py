from aiogram import types, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from developer.telegram.common.decorators import with_localization, with_localization_and_state
from developer.services import UserService, LanguageService, UserAgreementService, PrivacyPolicyService
from developer.database.session import db_manager
from developer.telegram.common.validators import Validator
from config import get_config
import logging

Config = get_config()

logger = logging.getLogger(__name__)

class RegistrationState(StatesGroup):
    InterfaceLanguageSelect = State()
    ConfirmUsageTerms = State()
    GetUsername = State()
    GetTimezone = State()
    SelectTimeFormat = State()
    GetConfirmationReceiveWords = State()
    GetConfirmationShareWords = State()
    GetConfirmationShareContact = State()
    GetConfirmationParticipateInChallenges = State()
    GetFinalConfirmation = State()



async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.callback_query(lambda c: c.data == "register")
    @with_localization_and_state
    async def registration_start(callback_query: types.CallbackQuery, state: FSMContext, t, k):
        # setting the state to the registration state
        await state.set_state(RegistrationState.InterfaceLanguageSelect)
        # answering the callback query
        await bot.answer_callback_query(callback_query.id)

        # deleting the keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        # creating a user_data dicitonary for the user
        user_data = {
            "telegram_id": callback_query.from_user.id,
        }

        # saving the user_data in the state
        await state.update_data(user_data=user_data)

        # getting locale
        current_locale = callback_query.from_user.language_code

        # getting keyboard context
        async with db_manager.get_session() as session:
            language_service = LanguageService(session)
            interface_languages = await language_service.get_interface_languages()

        ### creating language buttons out of interface_languages
        language_buttons = {}
        for interface_language in interface_languages:
            language_button = {
                interface_language.code: {'label': f'{interface_language.flag_code} {interface_language.get_name(interface_language.code)}'}
            }
            language_buttons.update(language_button)

        keyboard_context = {
            'callback_base': 'locale-selection',
            'buttons_in_a_row': 2,
            'buttons': language_buttons
        }

        # sending the language selection message
        await bot.send_message(
            callback_query.from_user.id,
            text=t('messages.registration.language_select', locale=current_locale),
            reply_markup=k('generate_language_selection_keyboard', locale=current_locale, context=keyboard_context),
            parse_mode="MarkdownV2",
            )

        # setting the state to usage terms confirmation
        await state.set_state(RegistrationState.ConfirmUsageTerms)


    @router.callback_query(lambda c: c.data.startswith("locale-selection_"), RegistrationState.ConfirmUsageTerms)
    @with_localization_and_state
    async def eula_privacy_confirmation(callback_query: types.CallbackQuery, state: FSMContext, t, k):
        # getting user's data from state
        state_data = await state.get_data()
        user_data = state_data.get("user_data", {})

        # getting selected locale
        locale = callback_query.data.split("_")[1]

        # saving the locale in the user_data
        new_user_data = {**user_data, "language_code": locale}

        # answering the callback query
        await bot.answer_callback_query(callback_query.id)

        # deleting the keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        # preparing the terms control
        terms_control = {
            'eula': False,
            'privacy': False
        }

        # storing the terms control in the state
        await state.update_data(terms_control=terms_control)

        # fetching active user_agreement and privacy_policy
        async with db_manager.get_session() as session:
            user_agreement_service = UserAgreementService(session)
            privacy_policy_service = PrivacyPolicyService(session)
            active_user_agreement = await user_agreement_service.get_active_agreement(new_user_data["language_code"])
            active_privacy_policy = await privacy_policy_service.get_active_policy(new_user_data["language_code"])

        # saving the active user_agreement and privacy_policy in the user_data
        new_user_data = {**new_user_data, "user_agreement": active_user_agreement, "privacy_policy": active_privacy_policy}

        # store new user_data in the state
        await state.update_data(user_data=new_user_data)

        # sending the terms of service message
        await bot.send_message(
            callback_query.from_user.id,
            text=t('messages.registration.terms_of_service',
                   eula_url=active_user_agreement.url,
                   privacy_url=active_privacy_policy.url,
                   locale=new_user_data["language_code"]),
            reply_markup=k('keyboards.terms_of_service.eula_false_privacy_false', locale=new_user_data["language_code"]),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )

        @router.callback_query(lambda c: c.data.startswith("terms_"), RegistrationState.ConfirmUsageTerms)
        @with_localization_and_state
        async def terms_confirmation(callback_query: types.CallbackQuery, state: FSMContext, t, k):
            # getting user's data from state
            state_data = await state.get_data()
            user_data = state_data.get("user_data", {})
            terms_control = state_data.get("terms_control", {})

            # answering the callback query
            await bot.answer_callback_query(callback_query.id)

            # getting selected terms
            terms = callback_query.data.split("_")[1]

            if terms == 'eula-true':
                # checking the consistency of the terms control
                if terms_control['eula']:
                    logger.error("EULA has been confirmed twice")

                # updating the terms control
                new_terms_control = {**terms_control, 'eula': True}
                await state.update_data(terms_control=new_terms_control)

                # refreshing the keyboard
                if not terms_control['privacy']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_true_privacy_false',
                                       locale=user_data["language_code"]))

                elif terms_control['privacy']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_true_privacy_true',
                                       locale=user_data["language_code"]))

            elif terms == 'privacy-true':
                # checking the consistency of the terms control
                if terms_control['privacy']:
                    logger.error("Privacy policy has been confirmed twice")

                # updating the terms control
                new_terms_control = {**terms_control, 'privacy': True}
                await state.update_data(terms_control=new_terms_control)

                # refreshing the keyboard
                if terms_control['eula']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_true_privacy_true',
                                       locale=user_data["language_code"]))

                elif not terms_control['eula']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_false_privacy_true',
                                       locale=user_data["language_code"]))

            elif terms == 'eula-false':
                # checking the consistency of the terms control
                if not terms_control['eula']:
                    logger.error("EULA has been rejected twice")

                # updating the terms control
                new_terms_control = {**terms_control, 'eula': False}
                await state.update_data(terms_control=new_terms_control)

                # refreshing the keyboard
                if terms_control['privacy']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_false_privacy_true',
                                       locale=user_data["language_code"]))

                elif not terms_control['privacy']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_false_privacy_false',
                                       locale=user_data["language_code"]))

            elif terms == 'privacy-false':
                # checking the consistency of the terms control
                if not terms_control['privacy']:
                    logger.error("Privacy policy has been rejected twice")

                # updating the terms control
                new_terms_control = {**terms_control, 'privacy': False}
                await state.update_data(terms_control=new_terms_control)

                # refreshing the keyboard
                if terms_control['eula']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_true_privacy_false',
                                       locale=user_data["language_code"]))

                elif not terms_control['eula']:
                    await callback_query.message.edit_reply_markup(
                        reply_markup=k('keyboards.terms_of_service.eula_false_privacy_false',
                                       locale=user_data["language_code"]))

            elif terms == 'proceed':
                # checking the consistency of the terms control
                if not terms_control['eula'] or not terms_control['privacy']:
                    logger.error("Terms of service have not been accepted")

                # remove terms control from the state
                state_data = await state.get_data()
                new_user_data = {**user_data, "agreed_to_terms_of_service": True}
                cleared_state_data = {k: v for k, v in state_data.items() if k != "terms_control"}
                new_state_data = {**cleared_state_data, "user_data": new_user_data}
                await state.set_data(new_state_data)

                # deleting the keyboard
                await callback_query.message.edit_reply_markup(reply_markup=None)

                # switching state
                await state.set_state(RegistrationState.GetUsername)

                # sending the username request message
                await bot.send_message(callback_query.from_user.id,
                                       text=t('messages.registration.username_request', locale=new_user_data["language_code"]),
                                       parse_mode="MarkdownV2"
                                       )
            else:
                logger.error("Unknown terms confirmation")


    @router.message(RegistrationState.GetUsername)
    @with_localization_and_state
    async def username_request(message: types.Message, state: FSMContext, t, k):
        # getting user's data from state
        state_data = await state.get_data()
        user_data = state_data.get("user_data", {})

        # getting username from the message
        received_username = Validator.validate_username(message.text)

        if not received_username:
            logger.error("Invalid username")
            await message.answer(text=t('messages.registration.incorrect_username', locale=user_data["language_code"]),
                                 parse_mode="MarkdownV2")
            return

        # saving the username in the user_data
        new_user_data = {**user_data, "username": received_username}

        # storing the new user_data in the state
        await state.update_data(user_data=new_user_data)

        # setting next state
        await state.set_state(RegistrationState.GetTimezone)
        await message.answer(
            text=t('messages.registration.get_users_timezone.initial_message',
                   username=new_user_data["username"],
                   locale=new_user_data["language_code"]),
            reply_markup=k('keyboards.get_users_timezone.initial_keyboard', locale=new_user_data["language_code"]),
            parse_mode="MarkdownV2"
        )