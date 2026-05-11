import { Component } from "react";

/**
 * Top-level safety net. A render error in any descendant lands here
 * instead of crashing the whole UI to a blank screen. The fallback is
 * intentionally plain — operators need a way to recover (reload), not
 * a debugging surface.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Surface to the browser console so devs see something during the
    // demo without exposing stack details to the user.
    if (typeof console !== "undefined") {
      console.error("UI error caught by ErrorBoundary:", error, info);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="error-boundary">
        <div className="error-boundary-card">
          <h1>Etwas ist schiefgelaufen</h1>
          <p>
            Die Oberfläche konnte nicht geladen werden. Versuche es bitte mit einem
            Neuladen — die Daten im Backend sind nicht betroffen.
          </p>
          <button type="button" className="primary-button" onClick={this.handleReload}>
            Seite neu laden
          </button>
        </div>
      </div>
    );
  }
}
