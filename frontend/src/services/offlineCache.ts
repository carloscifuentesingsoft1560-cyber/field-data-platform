import db from '../db/database'

import type {
  AuthUser,
} from '../types/auth'

import type {
  FieldOption,
} from '../types/fieldOption'

import type {
  Form,
} from '../types/form'

import type {
  FormField,
} from '../types/formField'

import type {
  FormVersion,
} from '../types/formVersion'

import type {
  Project,
} from '../types/project'


function buildKey(
  ownerUserId: number,
  entityId: number,
): string {
  return `${ownerUserId}:${entityId}`
}


export async function cacheUser(
  user: AuthUser,
): Promise<void> {
  await db.cachedUsers.put({
    owner_user_id: user.id,
    data: user,
    cached_at:
      new Date().toISOString(),
  })
}


export async function getCachedUser(
  ownerUserId: number,
): Promise<AuthUser | null> {
  const cached =
    await db.cachedUsers.get(
      ownerUserId,
    )

  return cached?.data ?? null
}


export async function cacheProjects(
  ownerUserId: number,
  projects: Project[],
): Promise<void> {
  await db.transaction(
    'rw',
    db.cachedProjects,
    async () => {
      await db.cachedProjects
        .where(
          'owner_user_id',
        )
        .equals(
          ownerUserId,
        )
        .delete()

      await db.cachedProjects.bulkPut(
        projects.map(
          (project) => ({
            cache_key:
              buildKey(
                ownerUserId,
                project.id,
              ),

            owner_user_id:
              ownerUserId,

            project_id:
              project.id,

            data:
              project,

            cached_at:
              new Date()
                .toISOString(),
          }),
        ),
      )
    },
  )
}


export async function
getCachedProjects(
  ownerUserId: number,
): Promise<Project[]> {
  const cached =
    await db.cachedProjects
      .where(
        'owner_user_id',
      )
      .equals(
        ownerUserId,
      )
      .toArray()

  return cached.map(
    (item) => item.data,
  )
}


export async function cacheForms(
  ownerUserId: number,
  forms: Form[],
): Promise<void> {
  await db.transaction(
    'rw',
    db.cachedForms,
    async () => {
      await db.cachedForms
        .where(
          'owner_user_id',
        )
        .equals(
          ownerUserId,
        )
        .delete()

      await db.cachedForms.bulkPut(
        forms.map(
          (form) => ({
            cache_key:
              buildKey(
                ownerUserId,
                form.id,
              ),

            owner_user_id:
              ownerUserId,

            project_id:
              form.project_id,

            form_id:
              form.id,

            data:
              form,

            cached_at:
              new Date()
                .toISOString(),
          }),
        ),
      )
    },
  )
}


export async function
getCachedFormsByProject(
  ownerUserId: number,
  projectId: number,
): Promise<Form[]> {
  const cached =
    await db.cachedForms
      .where(
        'owner_user_id',
      )
      .equals(
        ownerUserId,
      )
      .filter(
        (item) =>
          item.project_id ===
          projectId,
      )
      .toArray()

  return cached.map(
    (item) => item.data,
  )
}


export async function
getCachedProject(
  ownerUserId: number,
  projectId: number,
): Promise<Project | null> {
  const cached =
    await db.cachedProjects.get(
      buildKey(
        ownerUserId,
        projectId,
      ),
    )

  return cached?.data ?? null
}


export async function
cacheFormVersions(
  ownerUserId: number,
  formId: number,
  versions: FormVersion[],
): Promise<void> {
  await db.transaction(
    'rw',
    db.cachedFormVersions,
    async () => {
      const existing =
        await db.cachedFormVersions
          .where(
            'owner_user_id',
          )
          .equals(
            ownerUserId,
          )
          .filter(
            (item) =>
              item.form_id ===
              formId,
          )
          .toArray()

      await db.cachedFormVersions
        .bulkDelete(
          existing.map(
            (item) =>
              item.cache_key,
          ),
        )

      await db.cachedFormVersions
        .bulkPut(
          versions.map(
            (version) => ({
              cache_key:
                buildKey(
                  ownerUserId,
                  version.id,
                ),

              owner_user_id:
                ownerUserId,

              form_id:
                formId,

              version_id:
                version.id,

              status:
                version.status,

              data:
                version,

              cached_at:
                new Date()
                  .toISOString(),
            }),
          ),
        )
    },
  )
}


export async function
getCachedPublishedVersion(
  ownerUserId: number,
  formId: number,
): Promise<FormVersion | null> {
  const cached =
    await db.cachedFormVersions
      .where(
        'owner_user_id',
      )
      .equals(
        ownerUserId,
      )
      .filter(
        (item) =>
          item.form_id === formId &&
          item.status ===
            'published',
      )
      .first()

  return cached?.data ?? null
}


export async function
cacheFormFields(
  ownerUserId: number,
  formVersionId: number,
  fields: FormField[],
): Promise<void> {
  await db.transaction(
    'rw',
    db.cachedFormFields,
    async () => {
      const existing =
        await db.cachedFormFields
          .where(
            'owner_user_id',
          )
          .equals(
            ownerUserId,
          )
          .filter(
            (item) =>
              item.form_version_id ===
              formVersionId,
          )
          .toArray()

      await db.cachedFormFields
        .bulkDelete(
          existing.map(
            (item) =>
              item.cache_key,
          ),
        )

      await db.cachedFormFields
        .bulkPut(
          fields.map(
            (field) => ({
              cache_key:
                buildKey(
                  ownerUserId,
                  field.id,
                ),

              owner_user_id:
                ownerUserId,

              form_version_id:
                formVersionId,

              field_id:
                field.id,

              field_order:
                field.field_order,

              data:
                field,

              cached_at:
                new Date()
                  .toISOString(),
            }),
          ),
        )
    },
  )
}


export async function
getCachedFormFields(
  ownerUserId: number,
  formVersionId: number,
): Promise<FormField[]> {
  const cached =
    await db.cachedFormFields
      .where(
        'owner_user_id',
      )
      .equals(
        ownerUserId,
      )
      .filter(
        (item) =>
          item.form_version_id ===
          formVersionId,
      )
      .sortBy(
        'field_order',
      )

  return cached.map(
    (item) => item.data,
  )
}


export async function
cacheFieldOptions(
  ownerUserId: number,
  formFieldId: number,
  options: FieldOption[],
): Promise<void> {
  await db.transaction(
    'rw',
    db.cachedFieldOptions,
    async () => {
      const existing =
        await db.cachedFieldOptions
          .where(
            'owner_user_id',
          )
          .equals(
            ownerUserId,
          )
          .filter(
            (item) =>
              item.form_field_id ===
              formFieldId,
          )
          .toArray()

      await db.cachedFieldOptions
        .bulkDelete(
          existing.map(
            (item) =>
              item.cache_key,
          ),
        )

      await db.cachedFieldOptions
        .bulkPut(
          options.map(
            (option) => ({
              cache_key:
                buildKey(
                  ownerUserId,
                  option.id,
                ),

              owner_user_id:
                ownerUserId,

              form_field_id:
                formFieldId,

              option_id:
                option.id,

              option_order:
                option.option_order,

              data:
                option,

              cached_at:
                new Date()
                  .toISOString(),
            }),
          ),
        )
    },
  )
}


export async function
getCachedFieldOptions(
  ownerUserId: number,
  formFieldId: number,
): Promise<FieldOption[]> {
  const cached =
    await db.cachedFieldOptions
      .where(
        'owner_user_id',
      )
      .equals(
        ownerUserId,
      )
      .filter(
        (item) =>
          item.form_field_id ===
          formFieldId,
      )
      .sortBy(
        'option_order',
      )

  return cached.map(
    (item) => item.data,
  )
}
export async function getCachedForm(
  ownerUserId: number,
  formId: number,
): Promise<Form | null> {
  const cached =
    await db.cachedForms.get(
      `${ownerUserId}:${formId}`,
    )

  return cached?.data ?? null
}