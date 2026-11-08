import { defineConfig } from "vite";
import { addonPlugin, defineAddonManifest } from "@pulsesync/addon-sdk/vite";
import addonConfig from "./addon.config.mjs";
export default defineConfig({
  plugins:[addonPlugin({manifest:defineAddonManifest(addonConfig),minify:false})]
});
