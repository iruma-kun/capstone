document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector("#sidebar");
  document.querySelector("[data-menu]")?.addEventListener("click", () => sidebar?.classList.toggle("open"));

  document.querySelectorAll("[data-open-dialog]").forEach((button) => {
    button.addEventListener("click", () => document.getElementById(button.dataset.openDialog)?.showModal());
  });
  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => document.getElementById(button.dataset.closeDialog)?.close());
  });
  document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
  });

  document.querySelectorAll("form").forEach((form) => {
    const matterSelect = form.querySelector("[data-task-matter]");
    const documentSelect = form.querySelector("[data-task-document]");
    if (!matterSelect || !documentSelect) return;
    const filterDocuments = () => {
      const matterId = matterSelect.value;
      Array.from(documentSelect.options).forEach((option) => {
        option.hidden = Boolean(option.value) && option.dataset.matterId !== matterId;
      });
      if (documentSelect.selectedOptions[0]?.hidden) documentSelect.value = "";
    };
    matterSelect.addEventListener("change", filterDocuments);
    filterDocuments();
  });
});

document.body.addEventListener("htmx:responseError", () => {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = "Something went wrong. Please try again.";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
});
