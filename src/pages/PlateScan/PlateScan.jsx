import React, { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Camera,
  CheckCircle2,
  XCircle,
  Loader2,
  ScanLine,
  Banknote,
  Car,
  User,
} from "lucide-react";
import UserPageHeader from "../../components/UserPageHeader";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import { formatMoney, resolveLocale } from "../../utils/formatNumbers";
import "./PlateScan.css";

function PlateScan({ adminMode = false }) {
  const { t, i18n } = useTranslation();
  const fileRef = useRef(null);
  const [scans, setScans] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [ownerUserId, setOwnerUserId] = useState("");
  const [walletBalance, setWalletBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null);
  const [lastGate, setLastGate] = useState(null);

  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");
  const fmtMoney = (n) => formatMoney(n, loc, egp);

  const scansUrl = adminMode ? ENDPOINTS.ADMIN_PLATE_SCANS : ENDPOINTS.PLATE_SCANS;
  const postUrl = adminMode ? ENDPOINTS.ADMIN_PLATE_SCANS : ENDPOINTS.PLATE_SCANS;

  const load = useCallback(async () => {
    setError("");
    try {
      if (adminMode) {
        const [scanRes, accountsRes] = await Promise.all([
          API.get(scansUrl, {
            params: ownerUserId ? { user_id: ownerUserId } : {},
          }),
          API.get(ENDPOINTS.ADMIN_ACCOUNTS),
        ]);
        setScans(scanRes.data || []);
        const acc = accountsRes.data || [];
        setAccounts(acc);
        if (acc.length && !ownerUserId) {
          setOwnerUserId(String(acc[0].id));
        }
        setWalletBalance(null);
      } else {
        const { data } = await API.get(ENDPOINTS.PLATE_SCANS);
        setScans(data || []);
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message || t("plateScan.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t, adminMode, scansUrl, ownerUserId]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  const onPickFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (adminMode && !ownerUserId) {
      setError(t("plateScan.selectUserFirst"));
      return;
    }
    setPreview(URL.createObjectURL(file));
    runScan(file);
  };

  const runScan = async (file) => {
    if (adminMode && !ownerUserId) {
      setError(t("plateScan.selectUserFirst"));
      return;
    }
    setScanning(true);
    setError("");
    setLastGate(null);
    const fd = new FormData();
    fd.append("image", file);
    if (adminMode) {
      fd.append("owner_user_id", ownerUserId);
    }
    try {
      const { data } = await API.post(postUrl, fd);
      setScans((prev) => [data, ...prev.filter((s) => s.id !== data.id)]);
      setPreview(data.annotated_image_url || preview);
      if (data.gate_pass) {
        setLastGate(data.gate_pass);
        if (data.gate_pass.wallet_balance != null) {
          setWalletBalance(data.gate_pass.wallet_balance);
        }
      }
    } catch (e) {
      const detail = e.response?.data?.detail || e.response?.data?.error_message;
      setError(detail || e.message || t("plateScan.scanError"));
    } finally {
      setScanning(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const selectedAccount = accounts.find((a) => String(a.id) === String(ownerUserId));

  return (
    <main className="wallet-main-content plate-scan-page">
      <UserPageHeader
        title={adminMode ? t("plateScan.adminTitle") : t("plateScan.title")}
        subtitle={adminMode ? t("plateScan.adminSubtitle") : t("plateScan.subtitle")}
        showFleetId={!adminMode}
      />

      {adminMode ? (
        <label className="plate-scan-owner-select">
          <span>
            <User size={16} aria-hidden /> {t("plateScan.assignToUser")}
          </span>
          <select
            value={ownerUserId}
            onChange={(e) => setOwnerUserId(e.target.value)}
            disabled={scanning}
          >
            {accounts.length === 0 ? (
              <option value="">{t("plateScan.noUsers")}</option>
            ) : (
              accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} — {a.email} ({a.fleet_id})
                </option>
              ))
            )}
          </select>
          {selectedAccount ? (
            <p className="plate-scan-owner-hint">{t("plateScan.ownerHint")}</p>
          ) : null}
        </label>
      ) : null}

      {walletBalance != null ? (
        <p className="plate-scan-wallet">
          <Banknote size={18} aria-hidden />
          {adminMode ? t("plateScan.ownerWalletBalance") : t("plateScan.walletBalance")}:{" "}
          <strong>{fmtMoney(walletBalance)}</strong>
          {selectedAccount ? (
            <span className="plate-scan-wallet-user">
              {" "}
              ({selectedAccount.name})
            </span>
          ) : null}
        </p>
      ) : null}

      {error ? (
        <p className="plate-scan-error" role="alert">
          {error}
        </p>
      ) : null}

      {lastGate ? (
        <section className="plate-scan-gate-result" role="status">
          <h2>{t("plateScan.gatePassTitle")}</h2>
          <p className="plate-scan-gate-fare">
            {t("plateScan.gateFare")}:{" "}
            <strong className="numeric-display">{fmtMoney(lastGate.fare_amount)}</strong>
          </p>
          <p
            className={
              lastGate.paid
                ? "plate-scan-gate-status plate-scan-gate-status--paid"
                : "plate-scan-gate-status plate-scan-gate-status--unpaid"
            }
          >
            {lastGate.paid ? t("plateScan.gatePaid") : t("plateScan.gateUnpaid")}
          </p>
          {adminMode && selectedAccount ? (
            <p className="plate-scan-gate-name">
              {t("plateScan.chargedTo", { name: selectedAccount.name })}
            </p>
          ) : lastGate.gate_name ? (
            <p className="plate-scan-gate-name">{lastGate.gate_name}</p>
          ) : null}
        </section>
      ) : null}

      {adminMode ? (
        <section className="plate-scan-upload-card">
          <div className="plate-scan-upload-icon" aria-hidden>
            <ScanLine size={32} />
          </div>
          <h2>{t("plateScan.uploadTitle")}</h2>
          <p>{t("plateScan.adminUploadHint")}</p>

          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="plate-scan-file-input"
            onChange={onPickFile}
            disabled={scanning || !ownerUserId}
          />
          <button
            type="button"
            className="plate-scan-upload-btn"
            onClick={() => fileRef.current?.click()}
            disabled={scanning || !ownerUserId}
          >
            {scanning ? (
              <>
                <Loader2 size={18} className="plate-scan-spin" /> {t("plateScan.scanning")}
              </>
            ) : (
              <>
                <Camera size={18} /> {t("plateScan.chooseImage")}
              </>
            )}
          </button>

          {preview ? (
            <img src={preview} alt="" className="plate-scan-preview" />
          ) : null}
        </section>
      ) : null}

      <section className="plate-scan-history">
        <h2>{adminMode ? t("plateScan.adminHistory") : t("plateScan.history")}</h2>
        {loading ? (
          <p>{t("common.processing")}</p>
        ) : scans.length === 0 ? (
          <p className="plate-scan-empty">{t("plateScan.noScans")}</p>
        ) : (
          <ul className="plate-scan-list">
            {scans.map((s) => (
              <li key={s.id} className="plate-scan-item">
                <div className="plate-scan-item__media">
                  {s.annotated_image_url ? (
                    <img src={s.annotated_image_url} alt="" />
                  ) : s.image_url ? (
                    <img src={s.image_url} alt="" />
                  ) : (
                    <div className="plate-scan-item__placeholder" />
                  )}
                </div>
                <div className="plate-scan-item__body">
                  {adminMode && s.owner_name ? (
                    <div className="plate-scan-item__row">
                      <span className="plate-scan-label">{t("plateScan.account")}</span>
                      <strong>{s.owner_name}</strong>
                    </div>
                  ) : null}
                  <div className="plate-scan-item__row">
                    <span className="plate-scan-label">{t("plateScan.detected")}</span>
                    <strong>{s.detected_plate_text || "—"}</strong>
                  </div>
                  <div className="plate-scan-item__row">
                    <span className="plate-scan-label">
                      <Car size={14} aria-hidden /> {t("plateScan.vehicleType")}
                    </span>
                    <strong>{s.detected_vehicle_type || "—"}</strong>
                  </div>
                  {s.vehicle_created ? (
                    <p className="plate-scan-item__new-vehicle">{t("plateScan.vehicleAdded")}</p>
                  ) : null}
                  {s.gate_pass?.fare_amount ? (
                    <div className="plate-scan-item__row">
                      <span className="plate-scan-label">{t("plateScan.gateFare")}</span>
                      <strong className="numeric-display">
                        {fmtMoney(s.gate_pass.fare_amount)}
                      </strong>
                    </div>
                  ) : null}
                  {s.gate_pass ? (
                    <div className="plate-scan-match">
                      {s.gate_pass.paid ? (
                        <>
                          <CheckCircle2 size={18} className="match-ok" />
                          {t("plateScan.gatePaid")}
                        </>
                      ) : (
                        <>
                          <XCircle size={18} className="match-no" />
                          {t("plateScan.gateUnpaid")}
                        </>
                      )}
                    </div>
                  ) : null}
                  {s.error_message ? (
                    <p className="plate-scan-item__err">{s.error_message}</p>
                  ) : null}
                  <time className="plate-scan-time">
                    {new Date(s.created_at).toLocaleString()}
                  </time>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

export default PlateScan;
