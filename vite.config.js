import {defineConfig} from 'vite';
export default defineConfig({base:'./',build:{target:'es2022',rollupOptions:{output:{manualChunks:{three:['three','three/addons/loaders/GLTFLoader.js','three/addons/loaders/DRACOLoader.js']}}}}});
