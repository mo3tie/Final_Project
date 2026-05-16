import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Camera, Loader2 } from "lucide-react";
import API from "../../../APi/axiosConfig";
import { ENDPOINTS } from "../../../APi/endpoints";
import "./AddVehicle.css";

function AddVehicle() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [vehicleType, setVehicleType] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [vehicleColor, setVehicleColor] = useState("");
  const [vehicleFile, setVehicleFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);

  const handleCancel = () => navigate(-1);

  const handleFileChange = (e) => {
    setError("");
    setVehicleFile(e.target.files?.[0] ?? null);
  };

  const handleAddVehicle = async (event) => {
    event.preventDefault();
    setError("");
    if (!vehicleFile) {
      setError(t("addVehicle.photoRequired"));
      return;
    }
    setLoading(true);
    const fd = new FormData();
    fd.append("image", vehicleFile);
    if (vehicleType) fd.append("vehicle_type", vehicleType);
    if (vehicleModel.trim()) fd.append("vehicle_model", vehicleModel.trim());
    if (vehicleColor.trim()) fd.append("vehicle_color", vehicleColor.trim());

    try {
      const { data } = await API.post(ENDPOINTS.PLATE_SCANS, fd);
      const plate = data.detected_plate_text || data.registered_plate;
      setToast({
        type: "success",
        message: t("addVehicle.successWithPlate", { plate: plate || "—" }),
      });
      setTimeout(() => navigate("/dashboard/profile"), 1400);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || t("addVehicle.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="wallet-main-content add-vehicle-main">
      <div className="add-vehicle-centered">
        <header className="add-vehicle-header">
          <h1>{t("addVehicle.title")}</h1>
          <p>{t("addVehicle.subtitleAi")}</p>
        </header>

        {error ? (
          <p className="add-vehicle-error" role="alert">
            {error}
          </p>
        ) : null}

        <section className="add-vehicle-card">
          <form className="add-vehicle-form" onSubmit={handleAddVehicle}>
            <p className="add-vehicle-ai-hint">{t("addVehicle.aiHint")}</p>

            <div className="add-vehicle-field-group">
              <span className="add-vehicle-label">{t("addVehicle.photo")}</span>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="add-vehicle-file-input"
                onChange={handleFileChange}
                required
              />
              <button
                type="button"
                className="add-vehicle-upload-btn"
                onClick={() => fileRef.current?.click()}
                disabled={loading}
              >
                {loading ? (
                  <Loader2 size={18} className="add-vehicle-spin" />
                ) : (
                  <Camera size={18} />
                )}
                {vehicleFile ? vehicleFile.name : t("addVehicle.choosePhoto")}
              </button>
            </div>

            <div className="add-vehicle-field-group">
              <label htmlFor="vehicle-type" className="add-vehicle-label">
                {t("addVehicle.type")}
              </label>
              <select
                id="vehicle-type"
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
                className="add-vehicle-select"
              >
                <option value="">{t("addVehicle.selectType")}</option>
                <option value="private-car">{t("addVehicle.types.privateCar")}</option>
                <option value="minibus">{t("addVehicle.types.minibus")}</option>
                <option value="bus">{t("addVehicle.types.bus")}</option>
                <option value="truck">{t("addVehicle.types.truck")}</option>
              </select>
            </div>

            <div className="add-vehicle-field-group">
              <label htmlFor="vehicle-model" className="add-vehicle-label">
                {t("addVehicle.model")}
              </label>
              <input
                id="vehicle-model"
                type="text"
                value={vehicleModel}
                onChange={(e) => setVehicleModel(e.target.value)}
                className="add-vehicle-input"
                placeholder={t("signup.phModel")}
              />
            </div>

            <div className="add-vehicle-field-group">
              <label htmlFor="vehicle-color" className="add-vehicle-label">
                {t("addVehicle.color")}
              </label>
              <input
                id="vehicle-color"
                type="text"
                value={vehicleColor}
                onChange={(e) => setVehicleColor(e.target.value)}
                className="add-vehicle-input"
                placeholder={t("signup.phColor")}
              />
            </div>

            <div className="add-vehicle-actions">
              <button type="button" className="add-vehicle-cancel-btn" onClick={handleCancel}>
                {t("common.cancel")}
              </button>
              <button type="submit" className="add-vehicle-submit-btn" disabled={loading}>
                {loading ? t("common.processing") : t("addVehicle.submit")}
              </button>
            </div>
          </form>
        </section>
      </div>

      {toast ? (
        <div className="add-vehicle-toast" role="alert">
          {toast.message}
        </div>
      ) : null}
    </main>
  );
}

export default AddVehicle;
