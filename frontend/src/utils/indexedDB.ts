import { openDB, IDBPDatabase } from 'idb';

const DB_NAME = 'into-the-repo';
const STORE_NAME = 'keyval-store';

let dbPromise: Promise<IDBPDatabase> | null = null;

if (typeof window !== 'undefined') {
  dbPromise = openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    },
  });
}

const DEBUG = false;

function log(...args: unknown[]) {
  if (DEBUG) console.log('[IndexedDB]', ...args);
}

export async function setItem<T>(key: string, value: T): Promise<void> {
  if (!dbPromise) return;
  try {
    const db = await dbPromise;
    await db.put(STORE_NAME, value, key);
    log(`setItem: Saved key="${key}"`);
  } catch (error) {
    console.error(`setItem error for key="${key}":`, error);
  }
}

export async function getItem<T>(key: string): Promise<T | undefined> {
  if (!dbPromise) return undefined;
  try {
    const db = await dbPromise;
    const result = await db.get(STORE_NAME, key);
    log(`getItem: Retrieved key="${key}"`, result);
    return result;
  } catch (error) {
    console.error(`getItem error for key="${key}":`, error);
    return undefined;
  }
}

export async function removeItem(key: string): Promise<void> {
  if (!dbPromise) return;
  try {
    const db = await dbPromise;
    await db.delete(STORE_NAME, key);
    log(`removeItem: Removed key="${key}"`);
  } catch (error) {
    console.error(`removeItem error for key="${key}":`, error);
  }
}

export async function clearAll(): Promise<void> {
  if (!dbPromise) return;
  try {
    const db = await dbPromise;
    await db.clear(STORE_NAME);
    log(`clearAll: Cleared all items in store "${STORE_NAME}"`);
  } catch (error) {
    console.error('clearAll error:', error);
  }
}
