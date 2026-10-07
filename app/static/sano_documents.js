(() => {
  "use strict";

  const root = document.querySelector('[data-sano-documents-page="true"]');
  if (!root) return;

  const api = "/api/product-core/v1";
  const byId = (id) => document.getElementById(id);
  const shellTranslations = byId("product-shell-translations");
  let translations = {};
  try {
    const parsed = JSON.parse(shellTranslations?.textContent || "{}");
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) translations = parsed;
  } catch (_) {}
  const t = (key, fallback = key) => typeof translations[key] === "string" && translations[key] ? translations[key] : fallback;
  const state = { people: [], person: null, documents: [], capabilities: {}, selected: null, editing: false, viewerGeneration: 0, personGeneration: 0, pdfDocument: null, pdfPageNumber: 1, pdfZoom: 1, pdfRenderGeneration: 0 };

  const csrfToken = () => document.cookie.split("; ").find((item) => item.startsWith("opencare_csrf="))?.split("=").slice(1).join("=") || "";
  const setStatus = (message = "", tone = "info") => {
    const target = byId("documents-status");
    target.textContent = message;
    target.className = `ui-notice ui-notice--${tone}`;
    target.hidden = !message;
  };
  const errorMessage = (response, body) => {
    if (response.status === 401) return t("status.session_expired", "Your session has expired. Sign in again.");
    if (response.status === 403) return t("status.action_unavailable", "This action is no longer available.");
    if (response.status === 404) return t("documents.person_unavailable", "This Person is no longer available.");
    if (response.status === 409) return t("documents.changed", "This document changed. Refresh the archive and try again.");
    if (response.status === 422) return t("status.check_values", "Check the entered values and try again.");
    return body?.detail || t("status.request_failed", "The request could not be completed. Try again.");
  };
  const request = async (path, options = {}) => {
    const method = (options.method || "GET").toUpperCase();
    const headers = { ...(options.headers || {}) };
    if (method !== "GET" && method !== "HEAD") headers["X-OpenCare-CSRF"] = csrfToken();
    if (["POST", "PUT", "PATCH"].includes(method) &&
        !(options.body instanceof ArrayBuffer) &&
        !(options.body instanceof FormData) &&
        !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    const url = path.startsWith("/api/") ? path : `${api}${path.startsWith("/") ? path : `/${path}`}`;
    const response = await fetch(url, { credentials: "same-origin", ...options, headers });
    let body = null;
    try { body = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(errorMessage(response, body));
    return body;
  };
  const setBusy = (button, busy) => { if (!button) return; button.disabled = busy; button.setAttribute("aria-busy", String(busy)); };
  const setShellPerson = () => {
    const target = byId("product-shell-person-status");
    if (target) target.textContent = state.person ? `${t("documents.viewing", "Viewing")} ${state.person.display_name}` : t("person.no_selection", "No person selected");
  };
  const safeText = (value, fallback = "") => typeof value === "string" && value ? value : fallback;
  const summaryProviderLabel = (providerId) => ({
    "opencare.openai_responses": t("documents.provider_openai", "OpenAI"),
    "opencare.openrouter": t("documents.provider_openrouter", "OpenRouter"),
    "opencare.ollama": t("documents.provider_ollama", "Ollama (local)"),
    "opencare.deterministic.local": t("documents.provider_local_test", "local demo provider"),
  }[providerId] || t("documents.selected_provider", "the selected provider"));
  const typeLabel = (documentItem) => {
    if (documentItem.document_kind === "pdf") return t("documents.pdf", "PDF");
    if (documentItem.document_kind === "image") return t("documents.image", "Image");
    return t("documents.text", "Text");
  };
  const processingLabel = (documentItem) => {
    const key = {
      pending: "documents.text_pending",
      processing: "documents.text_processing",
      ready: "documents.text_ready",
      unavailable: "documents.text_unavailable",
      failed: "documents.text_failed",
    }[documentItem.text_processing?.status];
    return key ? t(key) : "";
  };
  const dateLabel = (documentItem) => documentItem.document_date || t("documents.date_unknown", "Date unknown");
  const yearLabel = (year) => year === "unknown" ? t("documents.year_unknown", "Year unknown") : year;

  function renderPeople() {
    const selector = byId("documents-person-selector");
    selector.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = state.people.length ? t("documents.choose_person", "Choose a Person") : t("documents.no_people", "No accessible People");
    selector.append(placeholder);
    state.people.forEach((person) => {
      const option = document.createElement("option");
      option.value = person.person_id;
      option.textContent = person.display_name;
      option.selected = person.person_id === state.person?.person_id;
      selector.append(option);
    });
    selector.disabled = state.people.length === 0;
  }

  function metadataRow(label, value, technical = false) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value;
    if (technical) dd.className = "sano-documents__technical-value";
    return [dt, dd];
  }

  function documentCard(documentItem) {
    const card = document.createElement("article");
    card.className = "sano-documents__card";
    const top = document.createElement("div");
    top.className = "sano-documents__card-top";
    const typeBadge = document.createElement("span");
    typeBadge.className = "sano-documents__card-type";
    typeBadge.textContent = typeLabel(documentItem);
    typeBadge.setAttribute("aria-label", typeLabel(documentItem));
    const heading = document.createElement("h4");
    heading.textContent = safeText(documentItem.title, safeText(documentItem.original_filename, t("documents.untitled", "Untitled document")));
    top.append(typeBadge, heading);
    const meta = document.createElement("p");
    meta.className = "sano-documents__card-meta";
    const parts = [dateLabel(documentItem)];
    const pageCount = documentItem.extraction?.page_count || 0;
    if (pageCount > 0) parts.push(`${pageCount} ${t("documents.pages", "pages")}`);
    parts.forEach((value) => {
      const span = document.createElement("span");
      span.textContent = value;
      meta.append(span);
    });
    const actions = document.createElement("div");
    actions.className = "sano-documents__actions";
    const processing = processingLabel(documentItem);
    if (processing && documentItem.text_processing?.status !== "ready") {
      const status = document.createElement("p");
      status.className = `sano-documents__processing sano-documents__processing--${documentItem.text_processing.status}`;
      status.textContent = processing;
      card.append(status);
    }
    const open = document.createElement("button");
    open.type = "button";
    open.className = "ui-button ui-button--primary";
    open.textContent = t("documents.open", "Open");
    open.addEventListener("click", () => { void openViewer(documentItem, open); });
    const download = document.createElement("a");
    download.className = "ui-button ui-button--secondary";
    download.href = `${api}/people/${encodeURIComponent(state.person.person_id)}/documents/${encodeURIComponent(documentItem.source_id)}/download`;
    download.download = "";
    download.textContent = t("documents.download", "Download");
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "ui-button ui-button--secondary";
    edit.textContent = t("documents.edit", "Edit");
    edit.hidden = !state.capabilities.document_write;
    edit.addEventListener("click", () => { void openViewer(documentItem, edit, true); });
    actions.append(open, download, edit);
    if (["unavailable", "failed"].includes(documentItem.text_processing?.status) && state.capabilities.document_write) {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "ui-button ui-button--secondary";
      retry.textContent = t("documents.retry_text", "Try recognition again");
      retry.addEventListener("click", () => { void retryTextProcessing(documentItem, retry); });
      actions.append(retry);
    }
    card.append(top, meta, actions);
    return card;
  }

  function renderDocuments() {
    const query = byId("documents-search").value.trim().toLocaleLowerCase();
    const visible = state.documents.filter((item) => `${item.title || ""} ${item.original_filename || ""}`.toLocaleLowerCase().includes(query));
    const groups = new Map();
    visible.forEach((item) => {
      const year = item.document_date ? item.document_date.slice(0, 4) : "unknown";
      if (!groups.has(year)) groups.set(year, []);
      groups.get(year).push(item);
    });
    groups.forEach((items) => items.sort((left, right) => {
      if (left.document_date && right.document_date && left.document_date !== right.document_date) return right.document_date.localeCompare(left.document_date);
      if (left.document_date && !right.document_date) return -1;
      if (!left.document_date && right.document_date) return 1;
      return String(right.created_at || "").localeCompare(String(left.created_at || ""));
    }));
    const container = byId("documents-year-groups");
    container.replaceChildren();
    [...groups.keys()].sort((left, right) => {
      if (left === "unknown") return 1;
      if (right === "unknown") return -1;
      return Number(right) - Number(left);
    }).forEach((year) => {
      const section = document.createElement("section");
      section.className = "sano-documents__year";
      const heading = document.createElement("h3");
      heading.textContent = yearLabel(year);
      const cards = document.createElement("div");
      cards.className = "sano-documents__cards";
      groups.get(year).forEach((item) => cards.append(documentCard(item)));
      section.append(heading, cards);
      container.append(section);
    });
    byId("documents-archive").hidden = !state.person || visible.length === 0;
    byId("documents-empty").hidden = !state.person || visible.length > 0;
    byId("documents-empty-title").textContent = state.documents.length && !visible.length ? t("documents.no_search_results", "No matching documents") : t("documents.empty_title", "No documents yet");
  }

  let pdfjsPromise = null;
  const loadPdfjs = () => {
    if (!pdfjsPromise) {
      pdfjsPromise = import("/static/vendor/pdfjs/pdf.min.mjs").then((library) => {
        library.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.mjs";
        return library;
      });
    }
    return pdfjsPromise;
  };
  const viewerIsCurrent = (personId, sourceId, generation) => (
    state.viewerGeneration === generation
    && state.person?.person_id === personId
    && state.selected?.source_id === sourceId
  );
  async function renderPdfPage(personId, sourceId, generation) {
    const status = byId("documents-pdf-status");
    const pages = byId("documents-pdf-pages");
    pages.replaceChildren();
    const pageStatus = byId("documents-pdf-page-status");
    const previous = byId("documents-pdf-prev");
    const next = byId("documents-pdf-next");
    const pdf = state.pdfDocument;
    if (!pdf || !viewerIsCurrent(personId, sourceId, generation)) return;
    const pageNumber = state.pdfPageNumber;
    const renderGeneration = ++state.pdfRenderGeneration;
    const renderIsCurrent = () => viewerIsCurrent(personId, sourceId, generation) && renderGeneration === state.pdfRenderGeneration;
    byId("documents-pdf-zoom-out").disabled = state.pdfZoom <= 1;
    byId("documents-pdf-zoom-in").disabled = state.pdfZoom >= 3;
    previous.disabled = pageNumber <= 1;
    next.disabled = pageNumber >= pdf.numPages;
    pageStatus.textContent = `${t("documents.page", "Page")} ${pageNumber} / ${pdf.numPages}`;
    status.textContent = t("documents.loading_original", "Loading original…");
    try {
      const page = await pdf.getPage(pageNumber);
      if (!renderIsCurrent()) return;
      const viewport = page.getViewport({ scale: 1.35 * state.pdfZoom });
      const pageShell = document.createElement("div");
      pageShell.className = "sano-documents__pdf-page";
      pageShell.style.width = `${Math.min(pages.clientWidth, 832) * state.pdfZoom}px`;
      const canvas = document.createElement("canvas");
      canvas.width = Math.ceil(viewport.width);
      canvas.height = Math.ceil(viewport.height);
      canvas.setAttribute("aria-label", `${t("documents.page", "Page")} ${pageNumber}`);
      const label = document.createElement("span");
      label.className = "sano-documents__pdf-page-label";
      label.textContent = `${t("documents.page", "Page")} ${pageNumber} / ${pdf.numPages}`;
      pageShell.append(canvas, label);
      pages.append(pageShell);
      await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
      if (renderIsCurrent()) status.textContent = "";
    } catch (error) {
      if (!renderIsCurrent()) return;
      pages.replaceChildren();
      status.textContent = error instanceof Error ? error.message : t("documents.original_unavailable", "The original could not be opened.");
    }
  }

  async function renderPdf(original, personId, sourceId, generation) {
    const status = byId("documents-pdf-status");
    status.textContent = t("documents.loading_original", "Loading original…");
    try {
      const response = await fetch(original, { credentials: "same-origin" });
      if (!response.ok) throw new Error(t("documents.original_unavailable", "The original could not be opened."));
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (!viewerIsCurrent(personId, sourceId, generation)) return;
      const library = await loadPdfjs();
      if (!viewerIsCurrent(personId, sourceId, generation)) return;
      const pdf = await library.getDocument({ data: bytes }).promise;
      if (!viewerIsCurrent(personId, sourceId, generation)) { await pdf.destroy(); return; }
      state.pdfDocument = pdf;
      state.pdfPageNumber = 1;
      await renderPdfPage(personId, sourceId, generation);
    } catch (error) {
      if (!viewerIsCurrent(personId, sourceId, generation)) return;
      byId("documents-pdf-pages").replaceChildren();
      status.textContent = error instanceof Error ? error.message : t("documents.original_unavailable", "The original could not be opened.");
    }
  }

  async function openViewer(documentItem, trigger, edit = false) {
    state.selected = documentItem;
    state.editing = edit;
    if (state.pdfDocument) { void state.pdfDocument.destroy(); state.pdfDocument = null; }
    const generation = ++state.viewerGeneration;
    const rawPersonId = state.person.person_id;
    const personId = encodeURIComponent(rawPersonId);
    const sourceId = encodeURIComponent(documentItem.source_id);
    const original = `${api}/people/${personId}/documents/${sourceId}/original`;
    byId("documents-viewer-title").textContent = safeText(documentItem.title, safeText(documentItem.original_filename, t("documents.untitled", "Untitled document")));
    byId("documents-viewer-meta").textContent = `${dateLabel(documentItem)} · ${typeLabel(documentItem)}`;
    const textViewer = byId("documents-text-viewer");
    const pdfViewer = byId("documents-pdf-viewer");
    const imageViewer = byId("documents-image-viewer");
    const isText = documentItem.media_type === "text/plain" || documentItem.document_kind === "text";
    const isImage = documentItem.document_kind === "image" || documentItem.media_type?.startsWith("image/");
    state.pdfPageNumber = 1;
    state.pdfZoom = 1;
    textViewer.hidden = !isText;
    imageViewer.hidden = !isImage;
    pdfViewer.hidden = isText || isImage;
    textViewer.textContent = "";
    imageViewer.removeAttribute("src");
    byId("documents-download").href = `${api}/people/${personId}/documents/${sourceId}/download`;
    const technical = byId("documents-technical-list");
    technical.replaceChildren();
    [
      [t("documents.filename", "Original filename"), safeText(documentItem.original_filename, "")],
      [t("documents.source_id", "Source ID"), documentItem.source_id],
      [t("documents.hash", "SHA-256"), documentItem.content_hash],
      [t("documents.size", "Size"), `${documentItem.size_bytes} ${t("documents.bytes", "bytes")}`],
      [t("documents.media_type", "Media type"), documentItem.media_type],
      [t("documents.registered", "Registered"), documentItem.created_at],
      [t("documents.extraction", "Text layer status"), documentItem.extraction?.status || ""],
    ].forEach(([label, value]) => technical.append(...metadataRow(label, value, true)));
    byId("documents-edit-title").value = safeText(documentItem.title, safeText(documentItem.original_filename, ""));
    byId("documents-edit-date").value = documentItem.document_date || "";
    byId("documents-metadata-form").hidden = !edit || !state.capabilities.document_write;
    const summary = byId("documents-summary");
    summary.hidden = documentItem.text_processing?.status !== "ready" || !documentItem.extraction;
    resetSummaryPanel();
    byId("documents-ask-about").href = `/chat?source_id=${encodeURIComponent(documentItem.source_id)}`;
    byId("documents-ask-about").hidden = summary.hidden;
    byId("documents-viewer").hidden = false;
    byId("documents-viewer").scrollIntoView({ behavior: "smooth", block: "start" });
    if (isText) {
      textViewer.textContent = t("documents.loading_original", "Loading original…");
      try {
        const response = await fetch(original, { credentials: "same-origin" });
        if (!response.ok) throw new Error(t("documents.original_unavailable", "The original could not be opened."));
        const originalText = await response.text();
        if (viewerIsCurrent(rawPersonId, documentItem.source_id, generation)) textViewer.textContent = originalText;
      } catch (error) {
        if (viewerIsCurrent(rawPersonId, documentItem.source_id, generation)) textViewer.textContent = error instanceof Error ? error.message : t("documents.original_unavailable", "The original could not be opened.");
      }
    } else if (isImage) {
      imageViewer.src = original;
    } else {
      void renderPdf(original, rawPersonId, documentItem.source_id, generation);
    }
    if (!summary.hidden) void loadSummary(documentItem, generation);
    if (edit) byId("documents-edit-title").focus();
    else trigger?.focus();
  }

  function resetSummaryPanel() {
    byId("documents-summary-consent").hidden = true;
    byId("documents-summary-result").hidden = true;
    byId("documents-summary-start").hidden = false;
    byId("documents-summary-start").disabled = false;
    byId("documents-summary-status").textContent = "";
    byId("documents-summary-disclosure").textContent = "";
    byId("documents-summary-consent-check").checked = false;
    byId("documents-summary-confirm").disabled = true;
    byId("documents-ask-about").hidden = true;
  }

  const documentApiPath = (personId, sourceId) => `/people/${encodeURIComponent(personId)}/documents/${encodeURIComponent(sourceId)}`;
  function showSummaryConsent(prepared) {
    if (!prepared?.run_id || !prepared.disclosure) return false;
    const key = prepared.disclosure.external ? "documents.summary_disclosure_external" : "documents.summary_disclosure_local";
    byId("documents-summary-disclosure").textContent = t(key).replace("{provider}", summaryProviderLabel(prepared.disclosure.provider_id));
    const consentKey = prepared.disclosure.external
      ? "documents.summary_consent_check"
      : "documents.summary_consent_check_local";
    byId("documents-summary-consent-label").textContent = t(consentKey);
    byId("documents-summary-consent").hidden = false;
    byId("documents-summary-status").textContent = t("documents.summary_consent_required", "Choose whether to allow Sano to process this document.");
    byId("documents-summary-confirm").dataset.runId = prepared.run_id;
    byId("documents-summary-consent-check").checked = false;
    byId("documents-summary-confirm").disabled = true;
    return true;
  }
  function renderSummary(summary) {
    const result = summary?.result;
    const status = summary?.status;
    const statusLabel = {
      consent_required: t("documents.summary_consent_required", "Choose whether to allow Sano to process this document."),
      consented: t("documents.summary_consent_required", "Choose whether to allow Sano to process this document."),
      executing: t("documents.summary_processing", "Sano is preparing the description…"),
      failed: t("documents.summary_failed", "The description could not be created. The document remains saved. You can try again and give consent again."),
      completed: t("documents.summary_complete", "Description is ready."),
      partial: t("documents.summary_partial_status", "Only part of the extracted text was used to prepare the description."),
    }[status] || "";
    byId("documents-summary-status").textContent = statusLabel;
    if (!result) {
      if (status === "consent_required") showSummaryConsent(summary);
      return;
    }
    byId("documents-summary-start").hidden = true;
    byId("documents-summary-result").hidden = false;
    byId("documents-summary-text").textContent = result.summary || "";
    const fillList = (id, values) => {
      const list = byId(id);
      list.replaceChildren();
      (Array.isArray(values) ? values : []).forEach((value) => {
        const item = document.createElement("li");
        item.textContent = value;
        list.append(item);
      });
    };
    fillList("documents-summary-points", result.key_points);
    fillList("documents-summary-questions", result.discussion_questions);
    byId("documents-summary-coverage").textContent = result.coverage_complete
      ? t("documents.summary_all_pages", "All extracted text was used to prepare the description.")
      : t("documents.summary_partial", "Only part of the extracted text was used to prepare the description.");
  }

  async function loadSummary(documentItem, generation = state.viewerGeneration) {
    try {
      const data = await request(`${documentApiPath(state.person.person_id, documentItem.source_id)}/summary`);
      if (!viewerIsCurrent(state.person.person_id, documentItem.source_id, generation)) return;
      if (data) renderSummary(data);
      else byId("documents-summary-status").textContent = t("documents.summary_available", "You can ask Sano for an optional description.");
    } catch (error) {
      if (viewerIsCurrent(state.person.person_id, documentItem.source_id, generation)) {
        byId("documents-summary-status").textContent = error.message;
      }
    }
  }

  async function prepareSummary() {
    if (!state.person || !state.selected) return;
    const button = byId("documents-summary-start");
    setBusy(button, true);
    byId("documents-summary-status").textContent = t("documents.summary_preparing", "Preparing a secure preview…");
    try {
      const path = documentApiPath(state.person.person_id, state.selected.source_id);
      const prepared = await request(`${path}/summary/prepare`, { method: "POST" });
      if (prepared.result) { renderSummary(prepared); return; }
      if (!showSummaryConsent(prepared)) {
        renderSummary(prepared);
      }
    } catch (error) {
      byId("documents-summary-status").textContent = error.message;
    } finally { setBusy(button, false); }
  }

  async function confirmSummary() {
    if (!state.person || !state.selected) return;
    const button = byId("documents-summary-confirm");
    const runId = button.dataset.runId;
    if (!runId || !byId("documents-summary-consent-check").checked) return;
    setBusy(button, true);
    byId("documents-summary-status").textContent = t("documents.summary_processing", "Sano is preparing the description…");
    try {
      const path = documentApiPath(state.person.person_id, state.selected.source_id);
      const result = await request(`${path}/summary/runs/${encodeURIComponent(runId)}/consent`, { method: "POST" });
      byId("documents-summary-consent").hidden = true;
      renderSummary(result);
    } catch (error) {
      byId("documents-summary-consent").hidden = true;
      byId("documents-summary-status").textContent = `${error.message} ${t("documents.summary_new_consent", "Prepare another attempt to give consent again.")}`;
    } finally { setBusy(button, false); }
  }

  async function retryTextProcessing(documentItem, button) {
    if (!state.person) return;
    setBusy(button, true);
    try {
      await request(`${documentApiPath(state.person.person_id, documentItem.source_id)}/text-processing/retry`, { method: "POST" });
      setStatus(t("documents.text_pending", "Text recognition is waiting to start."), "info");
      await loadPerson(state.person.person_id);
      pollTextProcessing(documentItem.source_id, 5);
    } catch (error) {
      setStatus(error.message, "danger");
    } finally { setBusy(button, false); }
  }

  async function pollTextProcessing(sourceId, remaining) {
    if (remaining <= 0 || !state.person) return;
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 1200));
      const personId = state.person.person_id;
      const response = await request(`/people/${encodeURIComponent(personId)}/documents`);
      state.documents = Array.isArray(response?.documents) ? response.documents.filter((item) => item.person_id === personId) : [];
      renderDocuments();
      const current = state.documents.find((item) => item.source_id === sourceId);
      if (current && ["pending", "processing"].includes(current.text_processing?.status)) pollTextProcessing(sourceId, remaining - 1);
    } catch (_) {}
  }

  function closeViewer() {
    state.selected = null;
    state.editing = false;
    state.viewerGeneration += 1;
    if (state.pdfDocument) { void state.pdfDocument.destroy(); state.pdfDocument = null; }
    byId("documents-viewer").hidden = true;
    byId("documents-pdf-pages").replaceChildren();
    byId("documents-text-viewer").textContent = "";
    byId("documents-image-viewer").removeAttribute("src");
  }

  async function loadPerson(personId) {
    if (!personId) return;
    const person = state.people.find((item) => item.person_id === personId);
    if (!person) return;
    const generation = ++state.personGeneration;
    closeViewer();
    state.person = null;
    state.documents = [];
    byId("documents-upload-form").hidden = true;
    byId("documents-archive").hidden = true;
    setStatus(t("documents.loading", "Loading documents…"));
    try {
      await request("/api/family-access/v1/active-person", { method: "PUT", body: JSON.stringify({ person_id: personId }) });
      const [documents, capabilityResponse] = await Promise.all([
        request(`/people/${encodeURIComponent(personId)}/documents`),
        request(`/people/${encodeURIComponent(personId)}/workspace-capabilities`).catch(() => ({ capabilities: {} })),
      ]);
      if (generation !== state.personGeneration) return;
      state.person = person;
      state.documents = Array.isArray(documents?.documents) ? documents.documents.filter((item) => item.person_id === personId) : [];
      state.capabilities = capabilityResponse?.capabilities || {};
      byId("documents-selected-person").textContent = person.display_name;
      byId("documents-person-help").textContent = t("documents.person_help", "Documents are scoped to this Person.");
      byId("documents-controls").hidden = false;
      byId("documents-upload-form").hidden = !state.capabilities.document_write;
      setShellPerson();
      renderPeople();
      renderDocuments();
      setStatus(t("documents.loaded", "Archive loaded."), "success");
    } catch (error) {
      if (generation !== state.personGeneration) return;
      state.person = null;
      state.documents = [];
      byId("documents-controls").hidden = true;
      byId("documents-archive").hidden = true;
      byId("documents-empty").hidden = true;
      setShellPerson();
      setStatus(error instanceof Error ? error.message : t("status.request_failed", "The request could not be completed. Try again."), "danger");
    }
  }

  async function loadPeople() {
    try {
      const response = await request("/people");
      state.people = Array.isArray(response?.people) ? response.people : [];
      renderPeople();
      const activeId = byId("product-shell-person")?.dataset.activePersonId || "";
      const initial = state.people.find((item) => item.person_id === activeId) || state.people[0];
      if (initial) {
        byId("documents-person-selector").value = initial.person_id;
        await loadPerson(initial.person_id);
      } else {
        byId("documents-selected-person").textContent = t("documents.no_people", "No accessible People");
        setStatus(t("documents.no_people_help", "No accessible Person is available yet."), "info");
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t("status.request_failed", "The request could not be completed. Try again."), "danger");
    }
  }

  async function upload(event) {
    event.preventDefault();
    const file = byId("documents-file").files[0];
    if (!state.person || !file) return;
    const personId = state.person.person_id;
    const generation = state.personGeneration;
    const lowerName = file.name.toLocaleLowerCase();
    const isPdf = file.type === "application/pdf" || lowerName.endsWith(".pdf");
    const isText = file.type === "text/plain" || lowerName.endsWith(".txt");
    const isJpeg = file.type === "image/jpeg" || /\.jpe?g$/i.test(file.name);
    const isPng = file.type === "image/png" || lowerName.endsWith(".png");
    if (!isPdf && !isText && !isJpeg && !isPng) { setStatus(t("documents.file_type_error", "Choose a PDF, text, JPG, or PNG file."), "danger"); return; }
    const button = event.submitter;
    setBusy(button, true);
    try {
      const response = await request(`/people/${encodeURIComponent(personId)}/documents`, {
        method: "POST",
        body: await file.arrayBuffer(),
        headers: {
          "Content-Type": isPdf ? "application/pdf" : isText ? "text/plain" : isJpeg ? "image/jpeg" : "image/png",
          "X-OpenCare-Filename": encodeURIComponent(file.name),
        },
      });
      if (generation !== state.personGeneration) return;
      byId("documents-upload-form").reset();
      byId("documents-search").value = "";
      await loadPerson(personId);
      setStatus(response?.created === false ? t("documents.duplicate_saved", "This document was already saved; its metadata was kept.") : t("documents.saved", "Document saved."), "success");
      const saved = state.documents.find((item) => item.source_id === response?.document?.source_id) || state.documents[0];
      if (saved && ["pending", "processing"].includes(saved.text_processing?.status)) pollTextProcessing(saved.source_id, 8);
    } catch (error) {
      if (generation !== state.personGeneration) return;
      setStatus(error instanceof Error ? error.message : t("status.request_failed", "The request could not be completed. Try again."), "danger");
    } finally { setBusy(button, false); }
  }

  async function saveMetadata(event) {
    event.preventDefault();
    if (!state.person || !state.selected || !state.capabilities.document_write) return;
    const personId = state.person.person_id;
    const sourceId = state.selected.source_id;
    const generation = state.personGeneration;
    const button = event.submitter;
    setBusy(button, true);
    try {
      const nextTitle = byId("documents-edit-title").value.trim();
      const nextDate = byId("documents-edit-date").value || "";
      const currentDate = state.selected.document_date || "";
      const payload = { title: nextTitle };
      if (nextDate !== currentDate) payload.document_date = nextDate || null;
      const updated = await request(`/people/${encodeURIComponent(personId)}/documents/${encodeURIComponent(sourceId)}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (generation !== state.personGeneration) return;
      const index = state.documents.findIndex((item) => item.source_id === updated.source_id);
      if (index >= 0) state.documents[index] = updated;
      state.selected = updated;
      renderDocuments();
      void openViewer(updated, null, false);
      setStatus(t("documents.metadata_saved", "Document details saved."), "success");
    } catch (error) {
      if (generation !== state.personGeneration) return;
      setStatus(error instanceof Error ? error.message : t("status.request_failed", "The request could not be completed. Try again."), "danger");
    } finally { setBusy(button, false); }
  }

  byId("documents-person-selector").addEventListener("change", (event) => { void loadPerson(event.target.value); });
  byId("documents-search").addEventListener("input", renderDocuments);
  byId("documents-upload-form").addEventListener("submit", upload);
  byId("documents-metadata-form").addEventListener("submit", saveMetadata);
  byId("documents-close").addEventListener("click", closeViewer);
  byId("documents-pdf-prev").addEventListener("click", () => {
    if (!state.pdfDocument || state.pdfPageNumber <= 1 || !state.person || !state.selected) return;
    state.pdfPageNumber -= 1;
    void renderPdfPage(state.person.person_id, state.selected.source_id, state.viewerGeneration);
  });
  byId("documents-pdf-next").addEventListener("click", () => {
    if (!state.pdfDocument || state.pdfPageNumber >= state.pdfDocument.numPages || !state.person || !state.selected) return;
    state.pdfPageNumber += 1;
    void renderPdfPage(state.person.person_id, state.selected.source_id, state.viewerGeneration);
  });
  ["in", "out"].forEach((direction) => {
    byId(`documents-pdf-zoom-${direction}`).addEventListener("click", () => {
      if (!state.pdfDocument || !state.person || !state.selected) return;
      state.pdfZoom = Math.max(1, Math.min(3, state.pdfZoom + (direction === "in" ? 0.5 : -0.5)));
      void renderPdfPage(state.person.person_id, state.selected.source_id, state.viewerGeneration);
    });
  });
  byId("documents-cancel-edit").addEventListener("click", () => { if (state.selected) void openViewer(state.selected, null, false); });
  byId("documents-summary-start").addEventListener("click", () => { void prepareSummary(); });
  byId("documents-summary-consent-check").addEventListener("change", (event) => {
    byId("documents-summary-confirm").disabled = !event.target.checked;
  });
  byId("documents-summary-confirm").addEventListener("click", () => { void confirmSummary(); });
  byId("documents-summary-cancel").addEventListener("click", () => {
    byId("documents-summary-consent").hidden = true;
    byId("documents-summary-consent-check").checked = false;
    byId("documents-summary-status").textContent = t("documents.summary_cancelled", "No description was created.");
  });
  void loadPeople();
})();
