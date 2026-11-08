import {defineAddon} from "@pulsesync/addon-sdk";
import addonConfig from "../addon.config.mjs";
import {createCelikomSourceController} from "../../source-controller.mjs";

/**
 * Off by default: the secure Companion-owned resolve transport is not yet
 * available. This is a host-contract / packaging candidate ONLY. Never
 * claim the user is connected or playing a CELIKOM replacement.
 */
export default defineAddon({
  id: addonConfig.id,
  name: addonConfig.name,
  start: async api => {
    const controller = createCelikomSourceController({
      api,
      resolve: async () => null,
      allowedOrigin: "https://no-network-w14.invalid"
    });
    await controller.start();
    return () => {void controller.dispose()};
  }
});
