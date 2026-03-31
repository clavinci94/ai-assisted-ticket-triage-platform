import { useEffect, useRef } from "react";
import { showToast } from "../../application/notifications/toast";

const MessageBanner = ({
  variant,
  type,
  title,
  message,
  children,
  dismissible = true,
  onDismiss,
  autoHideDuration = 4200,
}) => {
  const firedRef = useRef(false);
  const content =
    typeof message === "string"
      ? message
      : typeof children === "string"
        ? children
        : children == null
          ? ""
          : String(children);

  useEffect(() => {
    if (firedRef.current) return;
    if (!title && !content) return;

    firedRef.current = true;

    showToast({
      title,
      message: content,
      variant,
      type,
      dismissible,
      autoHideDuration,
    });

    if (typeof onDismiss === "function" && autoHideDuration !== 0) {
      const timer = window.setTimeout(() => {
        onDismiss();
      }, autoHideDuration);

      return () => window.clearTimeout(timer);
    }

    return undefined;
  }, [title, content, variant, type, dismissible, autoHideDuration, onDismiss]);

  return null;
};

export default MessageBanner;
