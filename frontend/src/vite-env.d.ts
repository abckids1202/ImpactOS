interface ImportMetaEnv {
  readonly DEV: boolean;
  readonly VITE_API_URL?: string;
  readonly VITE_PUBLIC_INDEX?: string;
  readonly VITE_APP_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
