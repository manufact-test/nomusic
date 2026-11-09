// Space is reserved only while an inner panel actually overflows.
export function initScrollSpacing() {
  const regions = [...document.querySelectorAll(".account-content")];
  if (!regions.length) return;
  let pending = false;
  const measure = () => {
    pending = false;
    for (const region of regions) {
      const overflow = region.clientHeight > 0 && region.scrollHeight > region.clientHeight + 1;
      const value = overflow ? "true" : "false";
      if (region.dataset.scrollOverflow !== value) region.dataset.scrollOverflow = value;
    }
  };
  const schedule = () => { if (!pending) { pending = true; queueMicrotask(measure); } };
  const resize = new ResizeObserver(schedule);
  for (const region of regions) resize.observe(region);
  const mutation = new MutationObserver(schedule);
  mutation.observe(document.querySelector("main"), { subtree: true, childList: true, characterData: true,
    attributes: true, attributeFilter: ["hidden", "open", "data-auth-screen"] });
  document.addEventListener("toggle", schedule, true);
  window.addEventListener("resize", schedule);
  schedule();
}
