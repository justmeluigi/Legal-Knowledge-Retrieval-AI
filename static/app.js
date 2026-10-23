// Legal Knowledge Retrieval AI • Reactive Frontend Controller
// Demonstrating RAG, Semantic Search, Access Control (RBAC), and Grounded Abstention

let users = [];
let activeUserId = "david_executive";
let activeUser = null;
let indexedDocuments = [];

document.addEventListener("DOMContentLoaded", async () => {
  await loadUsers();
  await loadDocuments();
});

// Load Security Personas
async function loadUsers() {
  try {
    const res = await fetch("/api/users");
    const data = await res.json();
    users = data.users || [];

    const container = document.getElementById("personaDeck");
    container.innerHTML = "";

    users.forEach((u) => {
      const isSelected = u.user_id === activeUserId;
      if (isSelected) activeUser = u;

      const card = document.createElement("div");
      card.className = `persona-card ${isSelected ? "selected" : ""}`;
      card.id = `userCard_${u.user_id}`;

      let badgeClass = "badge-guest";
      if (u.role === "EMPLOYEE") badgeClass = "badge-employee";
      if (u.role === "LEGAL_COUNSEL") badgeClass = "badge-legal";
      if (u.role === "EXECUTIVE_BOARD") badgeClass = "badge-exec";

      const initials = u.name.split(" ").map(n => n[0]).join("").slice(0, 2);

      card.innerHTML = `
        <div class="persona-header">
          <div class="persona-avatar">${initials}</div>
          <span class="persona-role-badge ${badgeClass}">${u.role}</span>
        </div>
        <div class="persona-name">${u.name}</div>
        <div class="persona-title">${u.title}</div>
        <div class="persona-desc">${u.description}</div>
      `;

      card.onclick = () => selectUser(u.user_id);
      container.appendChild(card);
    });

    renderActiveClearanceDeck();
  } catch (err) {
    console.error("Failed to load users:", err);
  }
}

function selectUser(userId) {
  activeUserId = userId;
  activeUser = users.find(u => u.user_id === userId);

  document.querySelectorAll(".persona-card").forEach(c => c.classList.remove("selected"));
  const selectedCard = document.getElementById(`userCard_${userId}`);
  if (selectedCard) selectedCard.classList.add("selected");

  renderActiveClearanceDeck();
}

function renderActiveClearanceDeck() {
  const deck = document.getElementById("activeClearancesDeck");
  deck.innerHTML = "";

  if (!activeUser) return;

  activeUser.permitted_clearances.forEach(clr => {
    const pill = document.createElement("span");
    let tierClass = "tag-public";
    if (clr === "INTERNAL") tierClass = "tag-internal";
    if (clr === "LEGAL_COUNSEL") tierClass = "tag-legal";
    if (clr === "EXECUTIVE_BOARD") tierClass = "tag-exec";

    pill.className = `clearance-pill ${tierClass}`;
    pill.textContent = `Clearance: ${clr}`;
    deck.appendChild(pill);
  });
}

// Preset Test Inquiries
function applyPreset(num) {
  const input = document.getElementById("queryInput");

  if (num === 1) {
    // Public question
    input.value = "What is the maximum dollar value for gifts or hospitality employees can accept?";
  } else if (num === 2) {
    // Internal employee handbook
    input.value = "What is the maximum domestic travel meal reimbursement per diem rate?";
  } else if (num === 3) {
    // Legal DPA
    input.value = "Within how many hours must a Personal Data Breach be reported to Legal Counsel under the DPA?";
  } else if (num === 4) {
    // Executive Top Secret M&A
    input.value = "What is the agreed transaction valuation and executive golden parachute payout in Project Titan?";
  } else if (num === 5) {
    // Abstention test
    input.value = "What are the corporate liability policies regarding commercial spacecraft repair?";
  }

  submitQuery();
}

function handleQueryKey(e) {
  if (e.key === "Enter") {
    submitQuery();
  }
}

// Execute RAG Query
async function submitQuery() {
  const input = document.getElementById("queryInput");
  const query = input.value.trim();

  if (!query) {
    alert("Please enter a legal question or click a preset scenario.");
    return;
  }

  const btn = document.getElementById("submitQueryBtn");
  const spinner = document.getElementById("querySpinner");
  const caption = btn.querySelector(".btn-caption");

  btn.disabled = true;
  spinner.classList.remove("hidden");
  caption.textContent = "Retrieving Evidence...";

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        user_id: activeUserId,
        similarity_threshold: 0.38
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Query failed");
    }

    const data = await res.json();
    renderQueryResponse(data);
  } catch (err) {
    alert(`Retrieval Error: ${err.message}`);
    console.error(err);
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
    caption.textContent = "Ask Legal AI";
  }
}

// Render Results
function renderQueryResponse(res) {
  const resultsSection = document.getElementById("resultsSection");
  resultsSection.classList.remove("hidden");

  // Scroll smoothly to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  const bannerCard = document.getElementById("resultBannerCard");
  const statusBadge = document.getElementById("resStatusBadge");
  const evidenceBadge = document.getElementById("resEvidenceBadge");
  const answerText = document.getElementById("resAnswerText");
  const abstentionNotice = document.getElementById("resAbstentionNotice");
  const abstentionReason = document.getElementById("resAbstentionReason");

  // Meta items
  document.getElementById("resUserPersonaTag").textContent = `Role: ${res.user_role}`;
  document.getElementById("resRetrievedCountTag").textContent = `${res.documents_retrieved_count} Passages Grounded`;
  document.getElementById("resElapsedTag").textContent = `${res.processing_time_seconds}s (${res.provider_used})`;

  // Reset classes
  bannerCard.className = "result-banner-card";
  statusBadge.className = "status-badge";

  if (res.status === "ANSWERED") {
    bannerCard.classList.add("answered");
    statusBadge.classList.add("badge-answered");
    statusBadge.textContent = "VERIFIED ANSWER";

    evidenceBadge.textContent = `${res.evidence_strength} EVIDENCE`;
    abstentionNotice.classList.add("hidden");
  } else if (res.status === "PERMISSION_RESTRICTED") {
    bannerCard.classList.add("restricted");
    statusBadge.classList.add("badge-restricted");
    statusBadge.textContent = "PERMISSION RESTRICTED";

    evidenceBadge.textContent = "CLEARANCE DENIED";
    abstentionNotice.classList.remove("hidden");
    abstentionReason.textContent = res.abstention_reason || "Access to requested evidence is restricted by RBAC policy.";
  } else {
    // ABSTAINED
    bannerCard.classList.add("abstained");
    statusBadge.classList.add("badge-abstained");
    statusBadge.textContent = "ABSTAINED (NO EVIDENCE)";

    evidenceBadge.textContent = "INSUFFICIENT EVIDENCE";
    abstentionNotice.classList.remove("hidden");
    abstentionReason.textContent = res.abstention_reason || "Evidence in authorized documents falls below the confidence threshold.";
  }

  answerText.textContent = res.answer;

  // Render Citations
  renderCitations(res.citations);
}

function renderCitations(citations) {
  const container = document.getElementById("citationsDeck");
  container.innerHTML = "";

  if (!citations || citations.length === 0) {
    container.innerHTML = '<div class="apple-card" style="grid-column: 1/-1; text-align: center; color: var(--text-tertiary); padding: 2.5rem;">No citations available (insufficient or restricted evidence).</div>';
    return;
  }

  citations.forEach(c => {
    const card = document.createElement("div");
    card.className = "citation-card";

    let tierClass = "tag-public";
    if (c.clearance_level === "INTERNAL") tierClass = "tag-internal";
    if (c.clearance_level === "LEGAL_COUNSEL") tierClass = "tag-legal";
    if (c.clearance_level === "EXECUTIVE_BOARD") tierClass = "tag-exec";

    card.innerHTML = `
      <div class="citation-card-header">
        <span class="citation-source-doc">${escapeHtml(c.document_title)}</span>
        <div class="citation-badges-wrap">
          <span class="cite-page-badge">Page ${c.page}</span>
          <span class="cite-tier-badge ${tierClass}">${c.clearance_level}</span>
        </div>
      </div>

      <div class="citation-section-title">${escapeHtml(c.clause_section)}</div>

      <div class="citation-passage-box">
        <p class="citation-passage-quote">“${escapeHtml(c.verbatim_passage)}”</p>
      </div>

      <div class="citation-footer-row">
        <span class="relevance-score-tag">Similarity: ${(c.similarity_score * 100).toFixed(1)}%</span>
        <a href="/api/documents/${c.doc_id}/download" target="_blank" class="inspect-pdf-link">Download PDF ↗</a>
      </div>
    `;

    container.appendChild(card);
  });
}

// Corpus Modal
async function loadDocuments() {
  try {
    const res = await fetch("/api/documents");
    indexedDocuments = await res.json();
    const tbody = document.getElementById("corpusTableBody");
    tbody.innerHTML = "";

    indexedDocuments.forEach(doc => {
      let tierClass = "tag-public";
      if (doc.clearance_level === "INTERNAL") tierClass = "tag-internal";
      if (doc.clearance_level === "LEGAL_COUNSEL") tierClass = "tag-legal";
      if (doc.clearance_level === "EXECUTIVE_BOARD") tierClass = "tag-exec";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(doc.title)}</strong></td>
        <td>${escapeHtml(doc.category)}</td>
        <td><span class="clearance-pill ${tierClass}">${doc.clearance_level}</span></td>
        <td>${doc.total_pages} pages (${doc.total_chunks} chunks)</td>
        <td><a href="/api/documents/${doc.doc_id}/download" target="_blank" class="inspect-pdf-link">View PDF</a></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}

function toggleCorpusModal() {
  const modal = document.getElementById("corpusModal");
  modal.classList.toggle("hidden");
}

function closeCorpusModal(e) {
  if (e && e.target !== e.currentTarget && !e.target.classList.contains("sheet-close-btn")) return;
  document.getElementById("corpusModal").classList.add("hidden");
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
