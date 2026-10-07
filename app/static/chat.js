(() => {
  "use strict";
  const form = document.querySelector("#chat-form");
  const textarea = document.querySelector("#chat-question");
  const stream = document.querySelector("#message-stream");
  const emptyState = document.querySelector("#empty-state");
  const sendButton = document.querySelector("#send-button");
  const newChat = document.querySelector("#new-chat");
  const status = document.querySelector("#chat-status");
  const endpoint = document.body.dataset.chatEndpoint;
  const live = endpoint === "/api/chat";
  const documentSource = document.body.dataset.chatDocumentSource || "";
  const documentPerson = document.body.dataset.chatDocumentPerson || "";
  const activePerson = document.body.dataset.chatPerson || documentPerson;
  const sourcePicker = document.querySelector("#chat-source-picker");
  const sourceToggle = document.querySelector("#chat-select-document");
  const sourceStatus = document.querySelector("#chat-source-status");
  const sourceOptions = document.querySelector("#chat-source-options");
  let translations = {};
  try { translations = JSON.parse(document.querySelector("#product-shell-translations")?.textContent || "{}"); } catch (_) { translations = {}; }
  const t = (key, fallback) => typeof translations[key] === "string" ? translations[key] : (fallback || key);
  const csrfToken = () => document.cookie.split("; ").find((item) => item.startsWith("opencare_csrf="))?.split("=").slice(1).join("=") || "";
  let consentPending = false;
  let disclosureCounter = 0;
  const addText = (parent, tag, value) => { const element = document.createElement(tag); element.textContent = value == null ? "" : String(value); parent.append(element); return element; };
  const revealLatest = () => { const last = stream.lastElementChild; if (last && typeof last.scrollIntoView === "function") last.scrollIntoView({ block: "nearest" }); };
  /* Rows before cards: a definition row (dt term + dd value) on the
     shared .ui-row grammar. Returns the dd so callers can refine it. */
  const addDefRow = (list, term) => { const row = document.createElement("div"); row.className = "ui-row"; addText(row, "dt", term).className = "ui-row__title"; const value = document.createElement("dd"); value.className = "ui-row__meta"; row.append(value); list.append(row); return value; };
  const addFieldRows = (list, fields) => { const value = addDefRow(list, t("chat.fields", "Fields")); const names = Array.isArray(fields) && fields.length ? fields : null; if (!names) { value.textContent = t("chat.none", "none"); return; } const items = document.createElement("ul"); names.forEach((name) => addText(items, "li", name)); value.append(items); };
  const addList = (card, title, values) => { if (!Array.isArray(values) || !values.length) return; const section = document.createElement("section"); section.className = "answer-section"; addText(section, "h3", title); const list = document.createElement("ul"); values.forEach((value) => addText(list, "li", value)); section.append(list); card.append(section); };
  const focusSourcePicker = () => {
    if (!sourcePicker) return;
    sourcePicker.hidden = false;
    sourceToggle?.focus();
    sourceToggle?.click();
  };
  const addRecordContextAction = (card) => {
    if (!sourcePicker || documentSource) return;
    const action = addText(card, "button", t("chat.select_document", "Select a document"));
    action.type = "button";
    action.className = "ui-button ui-button--secondary chat-state__action";
    action.addEventListener("click", focusSourcePicker);
  };
  const addAnswer = (answer) => {
    const content = answer && typeof answer.answer === "object" ? { ...answer, ...answer.answer } : (answer || {});
    const emptyContext = content.reason_code === "record_context_empty";
    const refused = Boolean(content.status === "refused") && !emptyContext;
    const declined = Boolean(content.status === "declined");
    const failed = Boolean(content.status === "error");
    const message = document.createElement("article");
    message.className = "message";
    const card = document.createElement("div");
    card.className = emptyContext ? "chat-empty-context ui-notice ui-notice--info" : refused ? "chat-refusal ui-notice ui-notice--warning" : declined ? "chat-declined ui-notice ui-notice--info" : failed ? "chat-error ui-notice ui-notice--danger" : "chat-answer";
    if (emptyContext) addText(card, "h3", t("chat.empty_context_heading", "No confirmed records are available yet"));
    if (refused) addText(card, "h3", t("chat.refusal_heading", "OpenCare refused this request before contacting a provider"));
    if (declined) addText(card, "h3", t("chat.declined_heading", "Disclosure was not approved"));
    if (failed) addText(card, "h3", t("chat.error_heading", "This request did not complete"));
    addText(card, "p", content.answer || t("chat.answer_fallback", "No answer was returned."));
    if (Array.isArray(content.citations) && content.citations.length) {
      const section = document.createElement("section");
      section.className = "answer-section chat-evidence";
      addText(section, "h3", t("chat.sources", "Sources"));
      content.citations.forEach((citation) => {
        const row = document.createElement("div");
        row.className = "ui-row";
        addText(row, "span", citation.source_id).className = "ui-row__title";
        addText(row, "span", citation.claim).className = "ui-row__meta";
        section.append(row);
      });
      card.append(section);
    }
    addList(card, t("chat.unknown_information", "Unknown information"), content.unknowns);
    addList(card, t("chat.questions_clinician", "Questions for a clinician"), content.doctor_questions);
    addList(card, t("chat.boundaries", "Boundaries"), content.boundary_notices);
    if (emptyContext) {
      addText(card, "p", content.next_step || t("chat.record_context_empty_next", "Select an authorized document to ask about its recognized pages.")).className = "chat-state__next";
      addRecordContextAction(card);
    } else if (refused) {
      addText(card, "p", t("chat.refusal_next_step", "Safe next step: review the recorded sources in Workspace or ask a source-backed question instead.")).className = "chat-state__next";
    }
    message.append(card);
    stream.append(message);
    revealLatest();
  };
  const localizeRetention = (value) => { const normalized = typeof value === "string" ? value.replace(/[.]$/, "") : value; return normalized === "provider policy; OpenCare does not retain provider payloads" ? t("chat.retention_provider_policy", value) : value; };
  const headers = () => ({ "content-type": "application/json", ...(live ? { "X-OpenCare-CSRF": csrfToken() } : {}) });
  const errorCode = (payload) => payload?.error?.code || payload?.reason_code || payload?.code || "";
  const errorMessage = (response, payload) => {
    const code = errorCode(payload);
    if (response.status === 401 || code === "authentication_required") return t("chat.authentication_required", "Your session is no longer available. Sign in again.");
    if (code === "origin_rejected") return t("chat.origin_rejected", "This request was blocked because its origin was not allowed.");
    if (code === "csrf_rejected") return t("chat.csrf_rejected", "This request could not be verified. Refresh and try again.");
    if (["context_changed", "context_limit_exceeded", "evidence_scope_invalid", "provenance_missing", "provider_disclosure_denied"].includes(code)) return t("chat.runtime_failure", "Sano could not prepare this request. No provider was contacted.");
    if (response.status === 403 || ["scope_forbidden", "forbidden_access", "person_access_denied", "person_mismatch", "authorization_expired"].includes(code)) return t("chat.forbidden_access", "This request is no longer available for the selected Person.");
    if ([400, 415, 422].includes(response.status) || ["request_validation_failed", "malformed_request"].includes(code)) return t("chat.malformed_request", "Check the question and try again.");
    return t("chat.request_failed", "Sano could not complete this request. Try again.");
  };
  const request = async (path, body, method = "POST") => {
    const init = { method, credentials: "same-origin", headers: method === "GET" ? { ...(live ? { "X-OpenCare-CSRF": csrfToken() } : {}) } : headers() };
    if (body !== undefined) init.body = JSON.stringify(body);
    const response = await fetch(path, init);
    let payload = {};
    let invalidJson = false;
    try { payload = await response.json(); } catch (_) { invalidJson = true; }
    if (invalidJson && response.ok) {
      const error = new Error(t("chat.request_failed", "Sano could not complete this request. Try again."));
      error.code = "provider_runtime_failure";
      throw error;
    }
    if (!response.ok) { const error = new Error(errorMessage(response, payload)); error.code = errorCode(payload); throw error; }
    return payload;
  };
  const setSourceStatus = (message = "", tone = "info") => {
    if (!sourceStatus) return;
    sourceStatus.textContent = message;
    sourceStatus.className = `chat-source-status ui-notice ui-notice--${tone}`;
    sourceStatus.hidden = !message;
  };
  const sourceTitle = (item) => item.title || item.original_filename || t("documents.untitled", "Untitled document");
  const renderSourceOptions = (documents) => {
    if (!sourceOptions) return;
    sourceOptions.replaceChildren();
    if (!documents.length) {
      setSourceStatus(t("chat.documents_none", "No documents are available for this Person yet."));
      const records = addText(sourceOptions, "a", t("chat.use_confirmed_records", "Use confirmed records"));
      records.href = "/chat";
      records.className = "ui-button ui-button--secondary";
      sourceOptions.append(records);
      const archive = addText(sourceOptions, "a", t("chat.documents_open_archive", "Open Documents"));
      archive.href = "/documents";
      archive.className = "ui-button ui-button--secondary";
      sourceOptions.append(archive);
      return;
    }
    const records = addText(sourceOptions, "a", t("chat.use_confirmed_records", "Use confirmed records"));
    records.href = "/chat";
    records.className = "ui-button ui-button--secondary";
    sourceOptions.append(records);
    documents.forEach((item) => {
      const option = document.createElement("article");
      option.className = "chat-source-option";
      addText(option, "h3", sourceTitle(item));
      const processing = item.text_processing?.status || "unavailable";
      const ready = processing === "ready" && Number(item.extraction?.total_chars || 0) > 0;
      const meta = addText(option, "p", ready ? t("chat.document_ready", "Ready to ask about recognized pages") : ["pending", "processing"].includes(processing) ? t("chat.document_pending", "Text recognition is still in progress.") : t("chat.document_unavailable", "This document has no usable recognized text."));
      meta.className = "chat-source-option__status";
      if (ready) {
        const link = addText(option, "a", t("documents.ask_about", "Ask about this document"));
        link.href = `/chat?source_id=${encodeURIComponent(item.source_id)}`;
        link.className = "ui-button ui-button--primary";
        link.addEventListener("click", () => { if (sourceToggle) sourceToggle.disabled = true; });
        option.append(link);
      } else {
        const unavailable = addText(option, "button", t("documents.ask_about", "Ask about this document"));
        unavailable.type = "button";
        unavailable.className = "ui-button ui-button--secondary";
        unavailable.disabled = true;
        unavailable.setAttribute("aria-disabled", "true");
        option.append(unavailable);
      }
      sourceOptions.append(option);
    });
    setSourceStatus("");
  };
  const loadSourceOptions = async () => {
    if (!sourceOptions || !activePerson) return;
    sourceToggle.disabled = true;
    sourceToggle.setAttribute("aria-busy", "true");
    setSourceStatus(t("chat.documents_loading", "Loading accessible documents…"));
    try {
      const payload = await request(`/api/product-core/v1/people/${encodeURIComponent(activePerson)}/documents`, undefined, "GET");
      const documents = Array.isArray(payload?.documents) ? payload.documents.filter((item) => item && item.person_id === activePerson) : [];
      renderSourceOptions(documents);
      sourceOptions.hidden = false;
      sourceOptions.dataset.loaded = "true";
    } catch (error) {
      if (error?.code === "scope_forbidden" || error?.code === "forbidden_access") {
        sourcePicker.hidden = true;
        return;
      }
      setSourceStatus(error instanceof Error ? error.message : t("chat.request_failed", "Sano could not complete this request. Try again."), "danger");
    } finally {
      sourceToggle.disabled = false;
      sourceToggle.removeAttribute("aria-busy");
    }
  };
  sourceToggle?.addEventListener("click", () => {
    const expanded = sourceToggle.getAttribute("aria-expanded") === "true";
    sourceToggle.setAttribute("aria-expanded", String(!expanded));
    if (expanded) { sourceOptions.hidden = true; return; }
    sourceOptions.hidden = false;
    if (!sourceOptions.dataset.loaded) void loadSourceOptions();
  });
  /* Permanent record of what was approved, rendered adjacent to the answer. */
  const addPreview = (preview) => { const section = document.createElement("section"); section.className = "answer-section disclosure-preview"; addText(section, "h3", t("chat.disclosure_preview", "Disclosure preview")); const grid = document.createElement("dl"); grid.className = "chat-detail-grid"; addDefRow(grid, t("chat.provider", "Provider")).textContent = preview.provider_id || t("chat.provider", "Provider"); addDefRow(grid, t("chat.model", "Model")).textContent = preview.model_id || t("chat.not_specified", "not specified"); addDefRow(grid, t("chat.boundaries", "Boundaries")).textContent = preview.external ? t("chat.external_provider", "Selected authorized data may leave this OpenCare installation") : t("chat.local_provider", "Runs on this OpenCare installation"); const evidence = addDefRow(grid, t("chat.evidence_items", "Evidence items")); evidence.textContent = String(preview.evidence_count || 0); evidence.className = "ui-row__meta chat-count"; addDefRow(grid, t("chat.retention", "Retention")).textContent = localizeRetention(preview.retention) || t("chat.not_specified", "not specified"); addFieldRows(grid, preview.fields); section.append(grid); return section; };
  /* Inline disclosure confirmation stage. Resolves true on explicit
     approval, false on decline. Performs no network calls itself. */
  const showDisclosureConsent = (preview) => new Promise((resolve) => {
    consentPending = true;
    disclosureCounter += 1;
    const headingId = `chat-consent-title-${disclosureCounter}`;
    const message = document.createElement("article");
    message.className = "message";
    const stage = document.createElement("section");
    stage.className = "chat-consent";
    stage.setAttribute("role", "region");
    stage.setAttribute("aria-labelledby", headingId);
    const heading = addText(stage, "h3", t("chat.allow_disclosure", "Allow this exact disclosure?"));
    heading.id = headingId;
    heading.tabIndex = -1;
    addText(stage, "p", t("chat.consent_help", "Nothing is sent before you approve this exact disclosure.")).className = "chat-consent__help";
    const grid = document.createElement("dl");
    grid.className = "chat-detail-grid";
    addDefRow(grid, t("chat.provider", "Provider")).textContent = preview.provider_id || t("chat.provider", "Provider");
    addDefRow(grid, t("chat.model", "Model")).textContent = preview.model_id || t("chat.not_specified", "not specified");
    addDefRow(grid, t("chat.boundaries", "Boundaries")).textContent = preview.external ? t("chat.external", "External provider") : t("chat.local_only", "Local only");
    const evidence = addDefRow(grid, t("chat.evidence_items", "Evidence items"));
    evidence.textContent = String(preview.evidence_count || 0);
    evidence.className = "ui-row__meta chat-count";
    addDefRow(grid, t("chat.retention", "Retention")).textContent = localizeRetention(preview.retention) || t("chat.not_specified", "not specified");
    addFieldRows(grid, preview.fields);
    stage.append(grid);
    const actions = document.createElement("div");
    actions.className = "chat-consent__actions";
    const approve = addText(actions, "button", t("chat.approve_disclosure", "Approve this disclosure"));
    approve.type = "button";
    approve.className = "ui-button ui-button--primary";
    const cancel = addText(actions, "button", t("button.cancel", "Cancel"));
    cancel.type = "button";
    cancel.className = "ui-button ui-button--secondary";
    let settled = false;
    const settle = (decision) => { if (settled) return; settled = true; consentPending = false; approve.disabled = true; cancel.disabled = true; message.remove(); resolve(decision); };
    approve.addEventListener("click", () => { approve.setAttribute("aria-busy", "true"); settle(true); });
    cancel.addEventListener("click", () => settle(false));
    actions.append(approve, cancel);
    stage.append(actions);
    message.append(stage);
    stream.append(message);
    revealLatest();
    heading.focus();
  });
  const addReceipt = (metadata) => { const message = document.createElement("article"); message.className = "message"; const section = document.createElement("section"); section.className = "chat-receipt"; addText(section, "h3", t("chat.receipt", "Receipt")); const grid = document.createElement("dl"); grid.className = "chat-detail-grid"; const receiptId = addDefRow(grid, t("chat.receipt_id", "Receipt id")); receiptId.textContent = metadata.receipt_id || t("chat.recorded", "recorded"); receiptId.className = "ui-row__meta chat-receipt__id"; const statusValue = addDefRow(grid, t("chat.status", "status")); const badge = document.createElement("span"); badge.className = "ui-status"; badge.textContent = metadata.status || "unknown"; statusValue.append(badge); section.append(grid); message.append(section); stream.append(message); revealLatest(); };
  const finishWithReceipt = async (executionId, executed, receiptPath = null) => { addAnswer(executed); if (executed.receipt_id) { status.textContent = t("chat.status_receipt", "Finalizing the execution receipt…"); const receipt = await fetch(receiptPath || `/api/chat/executions/${encodeURIComponent(executionId)}/receipt`, { credentials: "same-origin", headers: { "X-OpenCare-CSRF": csrfToken() } }); if (receipt.ok) addReceipt(await receipt.json()); } };
  const sendLive = async (question) => {
    if (documentSource && documentPerson) {
      const base = `/api/product-core/v1/people/${encodeURIComponent(documentPerson)}/documents/${encodeURIComponent(documentSource)}/questions`;
      const prepared = await request(`${base}/prepare`, { question });
      if (prepared.status === "refused") { addAnswer({ status: "refused", answer: prepared.answer, reason_code: prepared.reason_code, citations: [], unknowns: [], doctor_questions: [], boundary_notices: [] }); return; }
      const preview = prepared.preview || {};
      status.textContent = t("chat.status_await_consent", "Waiting for your explicit approval…");
      if (!await showDisclosureConsent(preview)) {
        addAnswer({ status: "declined", answer: t("chat.consent_declined", "No provider call was made because disclosure was not approved."), boundary_notices: [t("chat.consent_not_granted", "Consent was not granted.")], citations: [], unknowns: [], doctor_questions: [] });
        return;
      }
      status.textContent = t("chat.status_execute", "Executing the approved request…");
      const consented = await request(`${base}/${encodeURIComponent(prepared.execution_id)}/consent`, { question, fields: preview.fields || [] });
      const executed = await request(`${base}/${encodeURIComponent(consented.execution_id)}/execute`, { question });
      await finishWithReceipt(consented.execution_id, executed, `${base}/${encodeURIComponent(consented.execution_id)}/receipt`);
      return;
    }
    const prepared = await request("/api/chat/prepare", { question });
    if (prepared.status === "refused") { addAnswer(prepared); return; }
    const preview = prepared.preview || {};
    status.textContent = t("chat.status_await_consent", "Waiting for your explicit approval…");
    const approved = await showDisclosureConsent(preview);
    if (!approved) { status.textContent = ""; addAnswer({ status: "declined", answer: t("chat.consent_declined", "No provider call was made because disclosure was not approved."), boundary_notices: [t("chat.consent_not_granted", "Consent was not granted.")], citations: [], unknowns: [], doctor_questions: [] }); return; }
    textarea.focus(); status.textContent = t("chat.status_execute", "Executing the approved request…");
    const previewMessage = document.createElement("article"); previewMessage.className = "message"; previewMessage.append(addPreview(preview)); stream.append(previewMessage);
    await request(`/api/chat/executions/${prepared.execution_id}/consent`, { fields: preview.fields || [] });
    const executed = await request(`/api/chat/executions/${prepared.execution_id}/execute`, { question });
    await finishWithReceipt(prepared.execution_id, executed);
  };
  const sendDemo = async (question) => request(endpoint, { question }).then(addAnswer);
  const send = async (question) => { emptyState?.remove(); const message = document.createElement("article"); message.className = "message message-user"; const bubble = document.createElement("div"); bubble.className = "user-bubble"; const askLabel = documentSource ? "chat.document_ask_label" : "chat.ask_label"; addText(message, "h2", t(askLabel, "Your question")).className = "sr-only"; bubble.textContent = question; message.append(bubble); stream.append(message); revealLatest(); textarea.value = ""; sendButton.disabled = true; if (newChat) newChat.disabled = true; status.textContent = live ? t("chat.status_prepare", "Preparing an exact disclosure…") : t("chat.status_check", "Checking vault context and sources…"); try { if (live) await sendLive(question); else await sendDemo(question); } catch (error) { addAnswer({ status: "error", answer: error instanceof Error ? error.message : t("chat.error", "OpenCare could not process this request."), citations: [], unknowns: [], doctor_questions: [], boundary_notices: [t("chat.no_provider_output", "No provider output was displayed.")] }); } finally { sendButton.disabled = false; if (newChat) newChat.disabled = false; consentPending = false; status.textContent = ""; textarea.focus(); revealLatest(); } };
  form?.addEventListener("submit", (event) => { event.preventDefault(); const question = textarea.value.trim(); if (question && !sendButton.disabled && !consentPending) send(question); });
  textarea?.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
  document.querySelectorAll(".prompt-button").forEach((button) => button.addEventListener("click", () => { textarea.value = button.textContent; textarea.focus(); }));
  newChat?.addEventListener("click", () => { if (newChat.disabled || consentPending) return; stream.replaceChildren(); const fresh = document.createElement("section"); fresh.className = "empty-state ui-empty-state"; fresh.id = "empty-state"; const titleKey = documentSource ? "chat.document_empty_title" : "chat.empty_title"; const introKey = documentSource ? "chat.document_empty_intro" : "chat.empty_intro"; addText(fresh, "h2", t(titleKey, "Ask about your recorded vault")); addText(fresh, "p", t(introKey, "OpenCare summarizes source-backed records, identifies unknown information, and prepares clinician discussion questions.")); addText(fresh, "p", t("chat.empty_safety", "Answers are policy-checked and validated before display. Validation cannot guarantee medical correctness.")); stream.append(fresh); textarea.value = ""; status.textContent = ""; });
})();
