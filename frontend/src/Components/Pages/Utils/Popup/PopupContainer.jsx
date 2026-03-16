import React from "react";
import Popup from "./Popup";

const PopupContainer = ({ popups, removePopup }) => {
  return (
    <div id="popup-container">
      {popups.map((popup) => (
        <Popup
          key={popup.id}
          message={popup.message}
          type={popup.type}
          onClose={() => removePopup(popup.id)}
        />
      ))}
    </div>
  );
};

export default PopupContainer;
