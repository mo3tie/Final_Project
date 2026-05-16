// src/pages/Wallet & Payment/RechargeWallet/RechargeWallet.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import API from "../../../APi/axiosConfig";
import { ENDPOINTS } from "../../../APi/endpoints";
import { formatChartMoney, resolveLocale } from "../../../utils/formatNumbers";
import "./RechargeWallet.css";

function firstRechargeError(data) {
  if (!data || typeof data !== "object") return null;
  if (typeof data.detail === "string") return data.detail;
  for (const v of Object.values(data)) {
    if (Array.isArray(v) && v.length) return v[0];
    if (v && typeof v === "object") {
      const inner = firstRechargeError(v);
      if (inner) return inner;
    }
  }
  return null;
}

const QUICK_AMOUNTS = [10, 20, 50, 100];

function RechargeWallet() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [customAmount, setCustomAmount] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [toast, setToast] = useState(null); // { type: 'success' | 'error', message }
  
  // Payment form fields
  const [cardholderName, setCardholderName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [cvv, setCvv] = useState("");
  const [billingAddress, setBillingAddress] = useState("");
  const [saveCard, setSaveCard] = useState(false);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const getEffectiveAmount = () => {
    if (selectedAmount != null) return selectedAmount;
    const parsed = parseFloat(customAmount);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
  };

  const handleProceed = async () => {
    const amount = getEffectiveAmount();
    if (amount <= 0) {
      setToast({ type: "error", message: t("recharge.errAmount") });
      return;
    }
    if (!cardholderName || !cardNumber || !expiryDate || !cvv || !billingAddress) {
      setToast({ type: "error", message: t("recharge.errDetails") });
      return;
    }
    setIsProcessing(true);
    setToast(null);
    try {
      const rawCard = cardNumber.replace(/\D/g, "");
      await API.post(ENDPOINTS.WALLET_RECHARGE, {
        amount: amount.toFixed(2),
        cardholder_name: cardholderName.trim(),
        card_number: rawCard,
        expiry_date: expiryDate.trim(),
        cvv: cvv.replace(/\D/g, ""),
        billing_address: billingAddress.trim(),
      });
      const loc = resolveLocale(i18n.language);
      setToast({
        type: "success",
        message: t("recharge.success", { amount: formatChartMoney(amount, loc) }),
      });
      setSelectedAmount(null);
      setCustomAmount("");
      setCardholderName("");
      setCardNumber("");
      setExpiryDate("");
      setCvv("");
      setBillingAddress("");
      setSaveCard(false);
    } catch (err) {
      const msg = firstRechargeError(err.response?.data) || t("recharge.apiError");
      setToast({ type: "error", message: msg });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancel = () => {
    navigate("/dashboard/wallet");
  };

  // Format card number with spaces
  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || "";
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(" ");
    }
    return v;
  };

  const handleCardNumberChange = (e) => {
    const formatted = formatCardNumber(e.target.value);
    setCardNumber(formatted);
  };

  return (
    <main className="wallet-main-content">
        <header className="wallet-page-header recharge-header-row">
          <button
            type="button"
            className="recharge-back-btn"
            onClick={() => navigate("/dashboard/wallet")}
            aria-label={t("recharge.backAria")}
          >
            ←
          </button>
          <div>
            <h1>{t("recharge.title")}</h1>
            <p>{t("recharge.subtitle")}</p>
          </div>
        </header>

        <div className="recharge-two-columns">
          {/* LEFT COLUMN */}
          <div className="recharge-left-column">
            {/* Recharge Amount Card */}
            <section className="recharge-amount-card">
              <div className="recharge-card-header-blue">
                <h3 className="recharge-card-header-title">{t("recharge.amountTitle")}</h3>
              </div>
              <div className="recharge-card-body">
                <div className="recharge-amount-input-wrapper">
                  <input
                    id="recharge-amount-input"
                    type="number"
                    min="1"
                    step="0.01"
                    placeholder={t("recharge.amountPlaceholder")}
                    value={selectedAmount != null ? selectedAmount : customAmount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (selectedAmount != null) {
                        setSelectedAmount(null);
                        setCustomAmount(val);
                      } else {
                        setCustomAmount(val);
                      }
                    }}
                    className="recharge-amount-input"
                  />
                  <span className="recharge-amount-icon">💰</span>
                </div>
              </div>
            </section>

            {/* Card Preview */}
            <section className="recharge-card-preview-card">
              <h3 className="recharge-section-title">{t("recharge.cardPreview")}</h3>
              <div className="recharge-card-preview">
                <div className="recharge-card-preview-chip">💳</div>
                <div className="recharge-card-preview-visa">VISA</div>
                <div className="recharge-card-preview-number">
                  {cardNumber || "**** **** **** ****"}
                </div>
              </div>
            </section>
          </div>

          {/* RIGHT COLUMN */}
          <div className="recharge-right-column">
            <section className="recharge-payment-form-section">
              <h3 className="recharge-section-title">{t("recharge.paymentTitle")}</h3>
              
              <div className="recharge-form-group">
                <label htmlFor="cardholder-name" className="recharge-form-label">
                  {t("recharge.cardholder")}
                </label>
                <input
                  id="cardholder-name"
                  type="text"
                  placeholder={t("recharge.cardholderPh")}
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value)}
                  className="recharge-form-input"
                />
              </div>

              <div className="recharge-form-group">
                <label htmlFor="card-number" className="recharge-form-label">
                  {t("recharge.cardNumber")}
                </label>
                <div className="recharge-card-input-wrapper">
                  <input
                    id="card-number"
                    type="text"
                    placeholder="1234 5678 9012 3456"
                    value={cardNumber}
                    onChange={handleCardNumberChange}
                    maxLength={19}
                    className="recharge-form-input recharge-card-number-input"
                  />
                  <span className="recharge-visa-logo-small">VISA</span>
                </div>
              </div>

              <div className="recharge-form-row">
                <div className="recharge-form-group">
                  <label htmlFor="expiry-date" className="recharge-form-label">
                    {t("recharge.expiry")}
                  </label>
                  <input
                    id="expiry-date"
                    type="text"
                    placeholder="MM/YY"
                    value={expiryDate}
                    onChange={(e) => {
                      let val = e.target.value.replace(/\D/g, "");
                      if (val.length >= 2) {
                        val = val.substring(0, 2) + "/" + val.substring(2, 4);
                      }
                      setExpiryDate(val);
                    }}
                    maxLength={5}
                    className="recharge-form-input"
                  />
                </div>
                <div className="recharge-form-group">
                  <label htmlFor="cvv" className="recharge-form-label">
                    {t("recharge.cvv")}
                  </label>
                  <input
                    id="cvv"
                    type="text"
                    placeholder="123"
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").substring(0, 3))}
                    maxLength={3}
                    className="recharge-form-input"
                  />
                </div>
              </div>

              <div className="recharge-form-group">
                <label htmlFor="billing-address" className="recharge-form-label">
                  {t("recharge.billing")}
                </label>
                <textarea
                  id="billing-address"
                  placeholder={t("recharge.billingPh")}
                  value={billingAddress}
                  onChange={(e) => setBillingAddress(e.target.value)}
                  rows={3}
                  className="recharge-form-textarea"
                />
              </div>

              <div className="recharge-save-card-toggle">
                <label className="recharge-toggle-label">
                  <input
                    type="checkbox"
                    checked={saveCard}
                    onChange={(e) => setSaveCard(e.target.checked)}
                    className="recharge-toggle-input"
                  />
                  <span className="recharge-toggle-slider"></span>
                  <span className="recharge-toggle-text">{t("recharge.saveCard")}</span>
                </label>
              </div>
            </section>
          </div>
        </div>

        {/* FOOTER */}
        <div className="recharge-footer">
          <div className="recharge-footer-buttons">
            <button
              type="button"
              className="recharge-cancel-btn"
              onClick={handleCancel}
              disabled={isProcessing}
            >
              {t("common.cancel")}
            </button>
            <button
              type="button"
              className="recharge-proceed-btn"
              onClick={handleProceed}
              disabled={isProcessing}
            >
              {isProcessing ? t("common.processing") : t("recharge.proceed")}
            </button>
          </div>
          <div className="recharge-security-note">
            <span className="recharge-security-icon">🛡️</span>
            <span>{t("recharge.security")}</span>
          </div>
        </div>

        {toast && (
          <div
            className={`recharge-toast recharge-toast-${toast.type}`}
            role="alert"
          >
            {toast.type === "success" ? "✓ " : ""}
            {toast.message}
          </div>
        )}
    </main>
  );
}

export default RechargeWallet;
