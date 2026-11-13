import {defineConfig} from "vite";
import {addonPlugin, defineAddonManifest} from "@pulsesync/addon-sdk/vite";
import addonConfig from "./addon.config.mjs";

// Builds a real SDK artifact in Windows CI. This NEVER runs the official client.
export default defineConfig({
  plugins: [addonPlugin({manifest: defineAddonManifest(addonConfig), minify:false})]
});
