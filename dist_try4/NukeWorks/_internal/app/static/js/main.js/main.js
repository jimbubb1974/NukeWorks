// NukeWorks JavaScript

// Auto-dismiss flash messages after 5 seconds
document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});

// Confirm deletion actions
function confirmDelete(message) {
  return confirm(
    message ||
      "Are you sure you want to delete this item? This action cannot be undone."
  );
}

// Inline confirmation popup for delete icons
document.addEventListener("DOMContentLoaded", function () {
  const deleteButtons = document.querySelectorAll('[data-confirm="delete"]');
  let activePopup = null;

  function closeActivePopup() {
    if (activePopup) {
      activePopup.popup.classList.remove("show");
      activePopup = null;
    }
  }

  function buildPopup(form, trigger) {
    const popup = document.createElement("div");
    popup.className = "confirm-delete-popup shadow-sm";

    const title = document.createElement("div");
    title.className = "confirm-delete-title";
    title.textContent = trigger.dataset.confirmTitle || "Sure?";
    popup.appendChild(title);

    if (trigger.dataset.confirmMessage) {
      const message = document.createElement("div");
      message.className = "confirm-delete-message";
      message.textContent = trigger.dataset.confirmMessage;
      popup.appendChild(message);
    }

    const actions = document.createElement("div");
    actions.className = "confirm-delete-actions";

    const yesButton = document.createElement("button");
    yesButton.type = "button";
    yesButton.className = "btn btn-sm btn-danger";
    yesButton.textContent = trigger.dataset.confirmConfirmLabel || "Yes";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "btn btn-sm btn-secondary";
    cancelButton.textContent = trigger.dataset.confirmCancelLabel || "Cancel";

    actions.appendChild(yesButton);
    actions.appendChild(cancelButton);
    popup.appendChild(actions);

    form.appendChild(popup);

    yesButton.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      const submitter = trigger;
      closeActivePopup();
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit(submitter);
      } else {
        form.submit();
      }
    });

    cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      closeActivePopup();
    });

    return popup;
  }

  function openPopup(trigger) {
    const form = trigger.closest("form");
    if (!form) {
      return;
    }

    form.classList.add("confirm-delete-parent");
    let popup = form.querySelector(".confirm-delete-popup");
    if (!popup) {
      popup = buildPopup(form, trigger);
    }

    popup.classList.add("show");
    activePopup = { popup, trigger };
  }

  deleteButtons.forEach(function (button) {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      if (activePopup && activePopup.trigger === button) {
        closeActivePopup();
        return;
      }

      closeActivePopup();
      openPopup(button);
    });
  });

  document.addEventListener("click", function (event) {
    if (!activePopup) {
      return;
    }

    const clickedInsidePopup = event.target.closest(".confirm-delete-popup");
    const clickedTrigger = event.target.closest('[data-confirm="delete"]');

    if (!clickedInsidePopup && !clickedTrigger) {
      closeActivePopup();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeActivePopup();
    }
  });
});

// Form validation helper
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  }
}

// Initialize tooltips (Bootstrap)
document.addEventListener("DOMContentLoaded", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Initialize popovers (Bootstrap)
document.addEventListener("DOMContentLoaded", function () {
  const popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
});
