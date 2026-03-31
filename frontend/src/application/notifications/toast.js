const TOAST_ROOT_ID = "app-toast-root";
const DEFAULT_DURATION = 4200;

const normalizeVariant = (value) => {
  const input = String(value || "info").toLowerCase();
  if (["success", "error", "warning", "info"].includes(input)) return input;
  if (input === "danger") return "error";
  return "info";
};

const ensureRoot = () => {
  if (typeof document === "undefined") return null;

  let root = document.getElementById(TOAST_ROOT_ID);
  if (root) return root;

  root = document.createElement("div");
  root.id = TOAST_ROOT_ID;
  root.className = "toast-stack";
  document.body.appendChild(root);
  return root;
};

const createToastNode = ({
  title,
  message,
  variant = "info",
  autoHideDuration = DEFAULT_DURATION,
  dismissible = true,
}) => {
  const node = document.createElement("div");
  node.className = `toast toast--${normalizeVariant(variant)}`;
  node.setAttribute("role", "status");
  node.setAttribute("aria-live", "polite");

  const body = document.createElement("div");
  body.className = "toast__body";

  if (title) {
    const titleNode = document.createElement("div");
    titleNode.className = "toast__title";
    titleNode.textContent = title;
    body.appendChild(titleNode);
  }

  const messageNode = document.createElement("div");
  messageNode.className = "toast__message";
  messageNode.textContent = message || "";
  body.appendChild(messageNode);

  node.appendChild(body);

  if (dismissible) {
    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "toast__close";
    closeButton.setAttribute("aria-label", "Dismiss notification");
    closeButton.textContent = "×";
    closeButton.addEventListener("click", () => node.remove());
    node.appendChild(closeButton);
  }

  if (autoHideDuration !== 0) {
    window.setTimeout(() => {
      node.remove();
    }, autoHideDuration);
  }

  return node;
};

export const showToast = ({
  title,
  message,
  variant,
  type,
  autoHideDuration = DEFAULT_DURATION,
  dismissible = true,
}) => {
  if (typeof document === "undefined") return;

  const root = ensureRoot();
  if (!root) return;

  const resolvedMessage =
    typeof message === "string"
      ? message
      : message == null
        ? ""
        : String(message);

  if (!title && !resolvedMessage) return;

  const toastNode = createToastNode({
    title,
    message: resolvedMessage,
    variant: variant || type,
    autoHideDuration,
    dismissible,
  });

  root.appendChild(toastNode);
};

export const toast = {
  success: (message, title = "Success", options = {}) =>
    showToast({ title, message, variant: "success", ...options }),
  error: (message, title = "Error", options = {}) =>
    showToast({ title, message, variant: "error", ...options }),
  warning: (message, title = "Warning", options = {}) =>
    showToast({ title, message, variant: "warning", ...options }),
  info: (message, title = "Info", options = {}) =>
    showToast({ title, message, variant: "info", ...options }),
};
