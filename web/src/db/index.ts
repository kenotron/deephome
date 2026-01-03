import { createRxDatabase, addRxPlugin } from 'rxdb';
import { getRxStorageDexie } from 'rxdb/plugins/storage-dexie';
import { WIDGET_SCHEMA_LITERAL } from './schema';

// Add plugins
import { RxDBDevModePlugin } from 'rxdb/plugins/dev-mode';
// import { RxDBUpdatePlugin } from 'rxdb/plugins/update'; // if needed

if (import.meta.env.DEV) {
    addRxPlugin(RxDBDevModePlugin);
}

import { wrappedValidateAjvStorage } from 'rxdb/plugins/validate-ajv';
import { RxDBMigrationSchemaPlugin } from 'rxdb/plugins/migration-schema';
import { RxDBQueryBuilderPlugin } from 'rxdb/plugins/query-builder';
import { RxDBUpdatePlugin } from 'rxdb/plugins/update';

addRxPlugin(RxDBMigrationSchemaPlugin);
addRxPlugin(RxDBQueryBuilderPlugin);
addRxPlugin(RxDBUpdatePlugin);

export const initDB = async () => {
    const storage = import.meta.env.DEV
        ? wrappedValidateAjvStorage({ storage: getRxStorageDexie() })
        : getRxStorageDexie();

    const db = await createRxDatabase({
        name: 'deephome_db',
        storage,
        ignoreDuplicate: true
    });

    await db.addCollections({
        widgets: {
            schema: WIDGET_SCHEMA_LITERAL,
            migrationStrategies: {
                1: (oldDoc) => {
                    return oldDoc;
                },
                2: (oldDoc) => {
                    return {
                        ...oldDoc,
                        x: 0,
                        y: 0
                    };
                },
                3: (oldDoc) => {
                    // Ensure all version 3 fields exist
                    return {
                        ...oldDoc,
                        x: oldDoc.x ?? 0,
                        y: oldDoc.y ?? 0
                    };
                },
                4: (oldDoc) => {
                    return {
                        ...oldDoc,
                        url: oldDoc.url || null
                    };
                },
                5: (oldDoc) => {
                    return {
                        ...oldDoc,
                        sessionId: oldDoc.sessionId || null
                    };
                },
                6: (oldDoc) => {
                    return {
                        ...oldDoc,
                        projectPath: oldDoc.projectPath || null
                    };
                }
            }
        }
    });

    console.log('RxDB initialized');
    return db;
};
