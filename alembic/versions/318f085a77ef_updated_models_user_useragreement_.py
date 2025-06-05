"""Updated models User, UserAgreement, PrivacyPolicy, Language, LanguageTranslation

Revision ID: 318f085a77ef
Revises: 848db3a0ddfb
Create Date: 2025-06-05 21:22:11.709219

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '318f085a77ef'
down_revision: Union[str, None] = '848db3a0ddfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()

    # ### PHASE 1: CREATE NEW STRUCTURES ###

    # 1. Создаем промежуточную таблицу для изучаемых языков (если не существует)
    try:
        op.create_table('user_learning_languages',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('language_id', sa.Integer(), nullable=False),
            sa.Column('started_learning_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('finished_learning_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
            sa.ForeignKeyConstraint(['language_id'], ['languages.id'], name='fk_user_learning_languages_language_id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_learning_languages_user_id'),
            sa.PrimaryKeyConstraint('user_id', 'language_id')
        )
        print("Created user_learning_languages table")
    except Exception as e:
        print(f"user_learning_languages table might already exist: {e}")

    # 2. Создаем таблицу LanguageTranslation (если не существует)
    try:
        op.create_table('language_translations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('language_id', sa.Integer(), nullable=False),
            sa.Column('locale_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(32), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['language_id'], ['languages.id'], name='fk_language_translations_language_id'),
            sa.ForeignKeyConstraint(['locale_id'], ['languages.id'], name='fk_language_translations_locale_id'),
            sa.UniqueConstraint('language_id', 'locale_id', name='unique_language_translation_language_id_locale_id'),
            sa.UniqueConstraint('language_id', 'name', name='unique_language_translation_language_id_name'),
            sa.PrimaryKeyConstraint('id')
        )

        # Создаем индексы
        op.create_index('ix_language_translations_language_id', 'language_translations', ['language_id'])
        op.create_index('ix_language_translations_locale_id', 'language_translations', ['locale_id'])
        print("Created language_translations table")

    except Exception as e:
        print(f"language_translations table might already exist: {e}")
        # Если таблица существует, просто обновляем constraints
        with op.batch_alter_table('language_translations', schema=None) as batch_op:
            try:
                batch_op.drop_constraint('unique_language_translation_language_id_locale_id', type_='unique')
            except:
                pass
            try:
                batch_op.create_unique_constraint('unique_language_translation_language_id_locale_id', ['language_id', 'locale_id'])
                batch_op.create_unique_constraint('unique_language_translation_language_id_name', ['language_id', 'name'])
            except:
                pass

    # ### PHASE 2: BACKUP OLD DATA ###

    # Сохраняем существующие данные из languages для миграции
    try:
        existing_languages = connection.execute(sa.text("SELECT id, name, code FROM languages")).fetchall()
        print(f"Found {len(existing_languages)} existing languages to migrate")
    except Exception as e:
        print(f"Error reading existing languages: {e}")
        existing_languages = []

    # ### PHASE 3: MODIFY LANGUAGES TABLE ###

    with op.batch_alter_table('languages', schema=None) as batch_op:
        # Добавляем новые колонки
        batch_op.add_column(sa.Column('is_interface_language', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('flag_code', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))

        # Создаем индекс для code
        batch_op.create_index('ix_languages_code', ['code'], unique=True)

        # ВАЖНО: Сначала переносим данные в LanguageTranslation, потом удаляем name
        # Удаляем name в конце этой фазы

    # ### PHASE 4: MIGRATE OLD DATA TO NEW STRUCTURE ###

    # Переносим старые данные в LanguageTranslation
    for old_lang in existing_languages:
        try:
            # Создаем self-reference перевод (язык называется сам собой)
            connection.execute(sa.text("""
                INSERT INTO language_translations (language_id, locale_id, name)
                VALUES (:lang_id, :lang_id, :name)
            """), {
                'lang_id': old_lang.id,
                'name': old_lang.name
            })
            print(f"Migrated language {old_lang.code}: {old_lang.name}")
        except Exception as e:
            print(f"Error migrating language {old_lang.code}: {e}")

    # Теперь можно удалить name из languages
    with op.batch_alter_table('languages', schema=None) as batch_op:
        batch_op.drop_column('name')

    # ### PHASE 5: CREATE BASE LANGUAGES IF EMPTY ###

    # Проверяем количество языков
    result = connection.execute(sa.text("SELECT COUNT(*) FROM languages"))
    languages_count = result.scalar()

    if languages_count == 0:
        print("Creating base languages...")

        # Создаем базовые языки
        connection.execute(sa.text("""
            INSERT INTO languages (code, is_interface_language, flag_code) VALUES 
            ('en', 1, 'gb'),
            ('ru', 1, 'ru')
        """))

        # Получаем ID созданных языков
        en_result = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'en'"))
        en_id = en_result.scalar()

        ru_result = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'ru'"))
        ru_id = ru_result.scalar()

        # Создаем переводы названий
        translations = [
            # Английский язык
            {'language_id': en_id, 'locale_id': en_id, 'name': 'English'},      # EN на EN
            {'language_id': en_id, 'locale_id': ru_id, 'name': 'Английский'},   # EN на RU

            # Русский язык
            {'language_id': ru_id, 'locale_id': en_id, 'name': 'Russian'},      # RU на EN
            {'language_id': ru_id, 'locale_id': ru_id, 'name': 'Русский'},      # RU на RU
        ]

        for trans in translations:
            connection.execute(sa.text("""
                INSERT INTO language_translations (language_id, locale_id, name) 
                VALUES (:language_id, :locale_id, :name)
            """), trans)

        print(f"Created base languages: en_id={en_id}, ru_id={ru_id}")
    else:
        print(f"Languages already exist ({languages_count}), using existing data")
        # Получаем ID существующих языков
        en_result = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'en' LIMIT 1"))
        en_row = en_result.fetchone()
        en_id = en_row.id if en_row else None

        ru_result = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'ru' LIMIT 1"))
        ru_row = ru_result.fetchone()
        ru_id = ru_row.id if ru_row else None

        # Если нет английского языка, создаем его как fallback
        if not en_id:
            connection.execute(sa.text("""
                INSERT INTO languages (code, is_interface_language, flag_code) VALUES ('en', 1, 'gb')
            """))
            en_result = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'en'"))
            en_id = en_result.scalar()

            # Добавляем базовый перевод
            connection.execute(sa.text("""
                INSERT INTO language_translations (language_id, locale_id, name) 
                VALUES (:en_id, :en_id, 'English')
            """), {'en_id': en_id})

    # ### PHASE 6: UPDATE USER AGREEMENTS AND PRIVACY POLICIES ###

    # Обновляем UserAgreements
    with op.batch_alter_table('user_agreements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agreement_language_id', sa.Integer(), nullable=True))  # Сначала nullable
        batch_op.create_index('ix_user_agreements_agreement_language_id', ['agreement_language_id'])
        batch_op.create_foreign_key('fk_user_agreements_agreement_language_id', 'languages', ['agreement_language_id'], ['id'])

    # Переносим данные из language_code в agreement_language_id
    connection.execute(sa.text("""
        UPDATE user_agreements 
        SET agreement_language_id = (
            SELECT id FROM languages 
            WHERE code = user_agreements.language_code 
            LIMIT 1
        )
        WHERE agreement_language_id IS NULL
    """))

    # Устанавливаем fallback на английский для записей без соответствующего языка
    connection.execute(sa.text("""
        UPDATE user_agreements 
        SET agreement_language_id = :en_id 
        WHERE agreement_language_id IS NULL
    """), {'en_id': en_id})

    # Делаем поле обязательным и обновляем constraints
    with op.batch_alter_table('user_agreements', schema=None) as batch_op:
        batch_op.alter_column('agreement_language_id', nullable=False)
        batch_op.drop_constraint('unique_agreement_version_language_code', type_='unique')
        batch_op.create_unique_constraint('unique_agreement_version_language_id', ['version', 'agreement_language_id'])
        batch_op.drop_column('language_code')

    # Обновляем PrivacyPolicies аналогично
    with op.batch_alter_table('privacy_policies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('policy_language_id', sa.Integer(), nullable=True))  # Сначала nullable
        batch_op.create_index('ix_privacy_policies_policy_language_id', ['policy_language_id'])
        batch_op.create_foreign_key('fk_privacy_policies_policy_language_id', 'languages', ['policy_language_id'], ['id'])

    # Переносим данные из language_code в policy_language_id
    connection.execute(sa.text("""
        UPDATE privacy_policies 
        SET policy_language_id = (
            SELECT id FROM languages 
            WHERE code = privacy_policies.language_code 
            LIMIT 1
        )
        WHERE policy_language_id IS NULL
    """))

    # Устанавливаем fallback на английский
    connection.execute(sa.text("""
        UPDATE privacy_policies 
        SET policy_language_id = :en_id 
        WHERE policy_language_id IS NULL
    """), {'en_id': en_id})

    # Делаем поле обязательным и обновляем constraints
    with op.batch_alter_table('privacy_policies', schema=None) as batch_op:
        batch_op.alter_column('policy_language_id', nullable=False)
        batch_op.drop_constraint('unique_privacy_policy_version_language_code', type_='unique')
        batch_op.create_unique_constraint('unique_privacy_policy_version_language_id', ['version', 'policy_language_id'])
        batch_op.drop_column('language_code')

    # ### PHASE 7: CREATE BASE AGREEMENTS AND POLICIES IF EMPTY ###

    # Проверяем и создаем базовые UserAgreements
    result = connection.execute(sa.text("SELECT COUNT(*) FROM user_agreements"))
    agreements_count = result.scalar()

    if agreements_count == 0 and en_id:
        print("Creating base user agreements...")
        agreements_data = [
            {'version': '1.0', 'language_id': en_id, 'url': 'https://telegra.ph/Polzovatelskoe-soglashenie-05-30-20'},
        ]

        if ru_id:
            agreements_data.append(
                {'version': '1.0', 'language_id': ru_id, 'url': 'https://telegra.ph/Polzovatelskoe-soglashenie-05-30-20'}
            )

        for agreement in agreements_data:
            connection.execute(sa.text("""
                INSERT INTO user_agreements (version, agreement_language_id, url, is_active) 
                VALUES (:version, :language_id, :url, 1)
            """), agreement)

    # Проверяем и создаем базовые PrivacyPolicies
    result = connection.execute(sa.text("SELECT COUNT(*) FROM privacy_policies"))
    policies_count = result.scalar()

    if policies_count == 0 and en_id:
        print("Creating base privacy policies...")
        policies_data = [
            {'version': '1.0', 'language_id': en_id, 'url': 'https://telegra.ph/Polzovatelskoe-soglashenie-05-30-20'},
        ]

        if ru_id:
            policies_data.append(
                {'version': '1.0', 'language_id': ru_id, 'url': 'https://telegra.ph/Polzovatelskoe-soglashenie-05-30-20'}
            )

        for policy in policies_data:
            connection.execute(sa.text("""
                INSERT INTO privacy_policies (version, policy_language_id, url, is_active) 
                VALUES (:version, :language_id, :url, 1)
            """), policy)

    # ### PHASE 8: UPDATE USERS TABLE ###

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('interface_language_id', sa.Integer(), nullable=True))  # Сначала nullable
        batch_op.create_foreign_key('fk_users_interface_language_id', 'languages', ['interface_language_id'], ['id'])

    # Переносим данные из language_code в interface_language_id
    connection.execute(sa.text("""
        UPDATE users 
        SET interface_language_id = (
            SELECT id FROM languages 
            WHERE code = users.language_code 
            LIMIT 1
        )
        WHERE interface_language_id IS NULL
    """))

    # Устанавливаем fallback на английский
    connection.execute(sa.text("""
        UPDATE users 
        SET interface_language_id = :en_id 
        WHERE interface_language_id IS NULL
    """), {'en_id': en_id})

    # Делаем поле обязательным и удаляем старое
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('interface_language_id', nullable=False)
        batch_op.drop_column('language_code')

    print("Migration completed successfully!")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()

    # ### commands auto generated by Alembic - please adjust! ###

    # 1. Восстанавливаем language_code в users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language_code', sa.VARCHAR(length=10), nullable=True))

    # Восстанавливаем данные
    connection.execute(sa.text("""
        UPDATE users 
        SET language_code = (
            SELECT code FROM languages 
            WHERE languages.id = users.interface_language_id
        )
    """))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('language_code', nullable=False, server_default='en')
        batch_op.drop_constraint('fk_users_interface_language_id', type_='foreignkey')
        batch_op.drop_column('interface_language_id')

    # 2. Восстанавливаем language_code в user_agreements
    with op.batch_alter_table('user_agreements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language_code', sa.VARCHAR(length=10), nullable=True))

    connection.execute(sa.text("""
        UPDATE user_agreements 
        SET language_code = (
            SELECT code FROM languages 
            WHERE languages.id = user_agreements.agreement_language_id
        )
    """))

    with op.batch_alter_table('user_agreements', schema=None) as batch_op:
        batch_op.alter_column('language_code', nullable=False, server_default='en')
        batch_op.drop_constraint('fk_user_agreements_agreement_language_id', type_='foreignkey')
        batch_op.drop_constraint('unique_agreement_version_language_id', type_='unique')
        batch_op.drop_index('ix_user_agreements_agreement_language_id')
        batch_op.create_unique_constraint('unique_agreement_version_language_code', ['version', 'language_code'])
        batch_op.drop_column('agreement_language_id')

    # 3. Восстанавливаем language_code в privacy_policies
    with op.batch_alter_table('privacy_policies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language_code', sa.VARCHAR(length=10), nullable=True))

    connection.execute(sa.text("""
        UPDATE privacy_policies 
        SET language_code = (
            SELECT code FROM languages 
            WHERE languages.id = privacy_policies.policy_language_id
        )
    """))

    with op.batch_alter_table('privacy_policies', schema=None) as batch_op:
        batch_op.alter_column('language_code', nullable=False, server_default='en')
        batch_op.drop_constraint('fk_privacy_policies_policy_language_id', type_='foreignkey')
        batch_op.drop_constraint('unique_privacy_policy_version_language_id', type_='unique')
        batch_op.drop_index('ix_privacy_policies_policy_language_id')
        batch_op.create_unique_constraint('unique_privacy_policy_version_language_code', ['version', 'language_code'])
        batch_op.drop_column('policy_language_id')

    # 4. Восстанавливаем name в languages из LanguageTranslation
    with op.batch_alter_table('languages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=32), nullable=True))

    # Восстанавливаем name из LanguageTranslation (self-reference переводы)
    connection.execute(sa.text("""
        UPDATE languages 
        SET name = (
            SELECT name FROM language_translations 
            WHERE language_translations.language_id = languages.id 
            AND language_translations.locale_id = languages.id 
            LIMIT 1
        )
    """))

    with op.batch_alter_table('languages', schema=None) as batch_op:
        batch_op.alter_column('name', nullable=False, server_default='Unknown')
        batch_op.drop_index('ix_languages_code')
        batch_op.drop_column('created_at')
        batch_op.drop_column('flag_code')
        batch_op.drop_column('is_interface_language')

    # 5. Восстанавливаем старые constraints в language_translations
    with op.batch_alter_table('language_translations', schema=None) as batch_op:
        batch_op.drop_constraint('unique_language_translation_language_id_name', type_='unique')
        batch_op.drop_constraint('unique_language_translation_language_id_locale_id', type_='unique')
        try:
            batch_op.create_unique_constraint('unique_language_translation_language_id_locale_id', ['language_id', 'locale_id', 'name'])
        except:
            pass

    # 6. Удаляем промежуточную таблицу
    try:
        op.drop_table('user_learning_languages')
    except:
        pass

    # ### end Alembic commands ###