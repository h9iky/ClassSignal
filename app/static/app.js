"use strict";

const API_BASE = "/api/v1";
const state = { subjects: [], quarters: [], topics: [], editingTopic: null, toastTimer: null };

const elements = {
  connection: document.querySelector("#connection-status"),
  connectionLabel: document.querySelector("#connection-label"),
  topicList: document.querySelector("#topic-list"),
  subjectFilter: document.querySelector("#subject-filter"),
  quarterFilter: document.querySelector("#quarter-filter"),
  statusFilter: document.querySelector("#status-filter"),
  search: document.querySelector("#topic-search"),
  subjectList: document.querySelector("#subject-list"),
  quarterList: document.querySelector("#quarter-list"),
  subjectDialog: document.querySelector("#subject-dialog"),
  quarterDialog: document.querySelector("#quarter-dialog"),
  topicDialog: document.querySelector("#topic-dialog"),
  toast: document.querySelector("#toast"),
};

class ApiError extends Error {
  constructor(status, detail) {
    super("API request failed");
    this.status = status;
    this.detail = detail;
  }
}

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const responseText = await response.text();
  let payload = null;

  if (responseText) {
    try {
      payload = JSON.parse(responseText);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) throw new ApiError(response.status, payload?.detail);
  return payload;
}

function setConnection(online, label) {
  elements.connection.classList.toggle("is-online", online);
  elements.connection.classList.toggle("is-offline", !online);
  elements.connectionLabel.textContent = label;
}

function setText(selector, value) {
  document.querySelector(selector).textContent = String(value);
}

function addOption(select, value, label) {
  const option = document.createElement("option");
  option.value = String(value);
  option.textContent = label;
  select.append(option);
}

function fillFilter(select, items, placeholder, getLabel) {
  const previousValue = select.value;
  select.replaceChildren();
  addOption(select, "", placeholder);
  for (const item of items) addOption(select, item.id, getLabel(item));
  if (items.some((item) => String(item.id) === previousValue)) select.value = previousValue;
}

function fillTopicFormSelects() {
  const subjectSelect = document.querySelector("#topic-form [name='subject_id']");
  const quarterSelect = document.querySelector("#topic-form [name='quarter_id']");
  subjectSelect.replaceChildren();
  quarterSelect.replaceChildren();

  addOption(subjectSelect, "", "Выберите предмет");
  for (const subject of state.subjects) addOption(subjectSelect, subject.id, subject.name);

  addOption(quarterSelect, "", "Выберите четверть");
  for (const quarter of state.quarters) addOption(quarterSelect, quarter.id, quarterLabel(quarter));
}

function quarterLabel(quarter) {
  return `${quarter.number}-я четверть · ${quarter.school_year}`;
}

function renderStats() {
  setText("#stat-topics", state.topics.length);
  setText("#stat-published", state.topics.filter((topic) => topic.status === "published").length);
  setText("#stat-subjects", state.subjects.length);
  setText("#stat-quarters", state.quarters.length);
  setText("#subject-count-label", `${state.subjects.length} ${pluralize(state.subjects.length, "предмет", "предмета", "предметов")}`);
  setText("#quarter-count-label", `${state.quarters.length} ${pluralize(state.quarters.length, "четверть", "четверти", "четвертей")}`);
}

function pluralize(count, one, few, many) {
  const lastTwo = count % 100;
  const last = count % 10;
  if (lastTwo >= 11 && lastTwo <= 14) return many;
  if (last === 1) return one;
  if (last >= 2 && last <= 4) return few;
  return many;
}

function renderReferenceList(container, items, getTitle, getNote, emptyText) {
  container.replaceChildren();
  if (items.length === 0) {
    const empty = document.createElement("li");
    empty.className = "reference-empty";
    empty.textContent = emptyText;
    container.append(empty);
    return;
  }

  for (const item of items) {
    const row = document.createElement("li");
    const title = document.createElement("span");
    const note = document.createElement("small");
    title.textContent = getTitle(item);
    note.textContent = getNote(item);
    row.append(title, note);
    container.append(row);
  }
}

function renderStudyPlan() {
  renderReferenceList(
    elements.subjectList,
    state.subjects,
    (subject) => subject.name,
    (subject) => subject.description || "Предмет",
    "Предметов пока нет — добавьте первый.",
  );
  renderReferenceList(
    elements.quarterList,
    state.quarters,
    quarterLabel,
    (quarter) => quarter.starts_at ? `${quarter.starts_at}${quarter.ends_at ? ` — ${quarter.ends_at}` : ""}` : "Учебный период",
    "Четвертей пока нет — добавьте первую.",
  );
}

function makeEmptyState(title, description, buttons = []) {
  const empty = document.createElement("div");
  empty.className = "empty-state";

  const content = document.createElement("div");
  const icon = document.createElement("span");
  icon.className = "empty-state-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "✳";

  const heading = document.createElement("h3");
  heading.textContent = title;
  const detail = document.createElement("p");
  detail.textContent = description;
  content.append(icon, heading, detail);

  if (buttons.length) {
    const actions = document.createElement("div");
    actions.className = "empty-state-actions";
    for (const item of buttons) {
      const button = document.createElement("button");
      button.className = `button ${item.primary ? "button-primary" : "button-secondary"}`;
      button.type = "button";
      button.textContent = item.label;
      button.addEventListener("click", item.onClick);
      actions.append(button);
    }
    content.append(actions);
  }

  empty.append(content);
  return empty;
}

function renderTopics() {
  const search = elements.search.value.trim().toLocaleLowerCase("ru");
  const subjectId = elements.subjectFilter.value;
  const quarterId = elements.quarterFilter.value;
  const status = elements.statusFilter.value;

  const filtered = state.topics.filter((topic) => {
    const matchesSearch = !search || `${topic.title} ${topic.description || ""}`.toLocaleLowerCase("ru").includes(search);
    return matchesSearch
      && (!subjectId || String(topic.subject_id) === subjectId)
      && (!quarterId || String(topic.quarter_id) === quarterId)
      && (!status || topic.status === status);
  });

  elements.topicList.replaceChildren();
  elements.topicList.setAttribute("aria-busy", "false");

  if (state.subjects.length === 0 || state.quarters.length === 0) {
    elements.topicList.append(makeEmptyState(
      "Сначала подготовим учебный план",
      "Добавьте хотя бы один предмет и одну четверть, чтобы создать тему.",
      [
        { label: "Добавить предмет", onClick: openSubjectDialog },
        { label: "Добавить четверть", onClick: openQuarterDialog },
      ],
    ));
    return;
  }

  if (state.topics.length === 0) {
    elements.topicList.append(makeEmptyState(
      "Здесь появятся ваши темы",
      "Создайте первую тему и привяжите её к предмету и четверти.",
      [{ label: "Создать тему", primary: true, onClick: openTopicDialog }],
    ));
    return;
  }

  if (filtered.length === 0) {
    elements.topicList.append(makeEmptyState(
      "Ничего не нашлось",
      "Попробуйте изменить поисковый запрос или сбросить фильтры.",
      [{ label: "Сбросить фильтры", onClick: resetFilters }],
    ));
    return;
  }

  for (const topic of filtered) elements.topicList.append(makeTopicCard(topic));
}

function makeTopicCard(topic) {
  const card = document.createElement("article");
  card.className = "topic-card";

  const top = document.createElement("div");
  top.className = "topic-card-top";
  const subject = state.subjects.find((item) => item.id === topic.subject_id);
  const status = document.createElement("span");
  status.className = `status-pill status-${topic.status}`;
  status.textContent = ({ published: "Опубликовано", draft: "Черновик", archived: "В архиве" })[topic.status] || topic.status;
  const subjectLabel = document.createElement("span");
  subjectLabel.className = "topic-meta-label";
  subjectLabel.textContent = subject ? subject.name : "Предмет не найден";
  top.append(status, subjectLabel);

  const title = document.createElement("h3");
  title.textContent = topic.title;
  const description = document.createElement("p");
  description.className = "topic-card-description";
  description.textContent = topic.description || "Описание пока не добавлено.";

  const meta = document.createElement("div");
  meta.className = "topic-meta";
  const quarter = state.quarters.find((item) => item.id === topic.quarter_id);
  const quarterText = document.createElement("span");
  quarterText.textContent = quarter ? quarterLabel(quarter) : "Четверть не найдена";
  meta.append(quarterText);

  const bottom = document.createElement("div");
  bottom.className = "topic-card-bottom";
  const id = document.createElement("span");
  id.className = "topic-id";
  id.textContent = `ТЕМА №${topic.id}`;
  const edit = document.createElement("button");
  edit.className = "edit-topic-button";
  edit.type = "button";
  edit.textContent = "Изменить";
  edit.setAttribute("aria-label", `Изменить тему: ${topic.title}`);
  edit.addEventListener("click", () => openTopicDialog(topic));
  bottom.append(id, edit);

  card.append(top, title, description, meta, bottom);
  return card;
}

function resetFilters() {
  elements.search.value = "";
  elements.subjectFilter.value = "";
  elements.quarterFilter.value = "";
  elements.statusFilter.value = "";
  renderTopics();
}

async function refreshData() {
  const refreshButton = document.querySelector("#refresh-button");
  refreshButton.disabled = true;
  elements.topicList.setAttribute("aria-busy", "true");

  try {
    await apiRequest("/health");
    setConnection(true, "API подключён");

    const [subjects, quarters, topics] = await Promise.all([
      apiRequest("/subjects"),
      apiRequest("/quarters"),
      apiRequest("/topics"),
    ]);

    state.subjects = subjects;
    state.quarters = quarters;
    state.topics = topics;
    fillFilter(elements.subjectFilter, state.subjects, "Все предметы", (subject) => subject.name);
    fillFilter(elements.quarterFilter, state.quarters, "Все четверти", quarterLabel);
    fillTopicFormSelects();
    renderStats();
    renderStudyPlan();
    renderTopics();
  } catch (error) {
    setConnection(false, error instanceof TypeError ? "API недоступен" : "Не удалось загрузить данные");
    state.subjects = [];
    state.quarters = [];
    state.topics = [];
    fillFilter(elements.subjectFilter, [], "Все предметы", (subject) => subject.name);
    fillFilter(elements.quarterFilter, [], "Все четверти", quarterLabel);
    fillTopicFormSelects();
    renderStats();
    renderStudyPlan();
    elements.topicList.replaceChildren();
    elements.topicList.setAttribute("aria-busy", "false");
    const message = document.createElement("p");
    message.className = "inline-error";
    message.setAttribute("role", "alert");
    message.textContent = error instanceof TypeError
      ? "Не удалось подключиться к API. Проверьте, что сервер запущен, и нажмите «Обновить»."
      : "Не удалось загрузить учебные данные. Попробуйте обновить страницу.";
    elements.topicList.append(message);
  } finally {
    refreshButton.disabled = false;
  }
}

function openSubjectDialog() {
  clearFormError("subject-form-error");
  document.querySelector("#subject-form").reset();
  elements.subjectDialog.showModal();
  elements.subjectDialog.querySelector("[name='name']").focus();
}

function openQuarterDialog() {
  clearFormError("quarter-form-error");
  document.querySelector("#quarter-form").reset();
  elements.quarterDialog.showModal();
  elements.quarterDialog.querySelector("[name='school_year']").focus();
}

function openTopicDialog(topic = null) {
  if (state.subjects.length === 0 || state.quarters.length === 0) {
    showToast("Сначала добавьте предмет и четверть.", true);
    document.querySelector("#study-plan").scrollIntoView({ behavior: "smooth" });
    return;
  }

  state.editingTopic = topic;
  const form = document.querySelector("#topic-form");
  clearFormError("topic-form-error");
  form.reset();
  fillTopicFormSelects();

  document.querySelector("#topic-dialog-title").textContent = topic ? "Изменить тему" : "Новая тема";
  document.querySelector("#topic-submit-button").textContent = topic ? "Сохранить изменения" : "Создать тему";
  form.elements.title.value = topic?.title || "";
  form.elements.subject_id.value = topic ? String(topic.subject_id) : "";
  form.elements.quarter_id.value = topic ? String(topic.quarter_id) : "";
  form.elements.description.value = topic?.description || "";
  form.elements.status.value = topic?.status || "draft";
  elements.topicDialog.showModal();
  form.elements.title.focus();
}

function clearFormError(id) {
  const error = document.getElementById(id);
  error.hidden = true;
  error.textContent = "";
}

function showFormError(id, message) {
  const error = document.getElementById(id);
  error.textContent = message;
  error.hidden = false;
}

function apiErrorMessage(error) {
  if (!(error instanceof ApiError)) return "Не удалось связаться с сервером. Попробуйте ещё раз.";
  if (error.status === 409) return "Такая запись уже существует. Проверьте название и учебный год.";
  if (error.status === 404) return "Предмет или четверть больше не найдены. Обновите данные и повторите.";
  if (error.status === 422) {
    if (Array.isArray(error.detail)) {
      const field = error.detail[0]?.loc?.at(-1);
      const labels = { title: "название темы", name: "название предмета", school_year: "учебный год", number: "номер четверти" };
      const label = labels[field] || "поле";
      const issue = error.detail[0]?.msg;
      if (issue === "Field required") return `Заполните поле «${label}».`;
      return `Проверьте поле «${label}» и попробуйте ещё раз.`;
    }
    return typeof error.detail === "string" ? error.detail : "Проверьте введённые данные.";
  }
  return "Не удалось сохранить запись. Попробуйте ещё раз.";
}

function showToast(message, isError = false) {
  window.clearTimeout(state.toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.toggle("is-error", isError);
  elements.toast.hidden = false;
  state.toastTimer = window.setTimeout(() => { elements.toast.hidden = true; }, 3600);
}

async function submitSubject(event) {
  event.preventDefault();
  clearFormError("subject-form-error");
  const form = event.currentTarget;
  const values = new FormData(form);

  try {
    await apiRequest("/subjects", {
      method: "POST",
      body: JSON.stringify({ name: values.get("name"), description: values.get("description") || null }),
    });
    elements.subjectDialog.close();
    await refreshData();
    showToast("Предмет добавлен в учебный план.");
  } catch (error) {
    showFormError("subject-form-error", apiErrorMessage(error));
  }
}

async function submitQuarter(event) {
  event.preventDefault();
  clearFormError("quarter-form-error");
  const form = event.currentTarget;
  const values = new FormData(form);

  try {
    await apiRequest("/quarters", {
      method: "POST",
      body: JSON.stringify({
        school_year: values.get("school_year"),
        number: Number(values.get("number")),
        starts_at: values.get("starts_at") || null,
        ends_at: values.get("ends_at") || null,
      }),
    });
    elements.quarterDialog.close();
    await refreshData();
    showToast("Четверть добавлена в учебный план.");
  } catch (error) {
    showFormError("quarter-form-error", apiErrorMessage(error));
  }
}

async function submitTopic(event) {
  event.preventDefault();
  clearFormError("topic-form-error");
  const form = event.currentTarget;
  const values = new FormData(form);
  const payload = {
    title: values.get("title"),
    subject_id: Number(values.get("subject_id")),
    quarter_id: Number(values.get("quarter_id")),
    description: values.get("description") || null,
    status: values.get("status"),
  };

  try {
    if (state.editingTopic) {
      await apiRequest(`/topics/${state.editingTopic.id}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await apiRequest("/topics", { method: "POST", body: JSON.stringify(payload) });
    }
    elements.topicDialog.close();
    state.editingTopic = null;
    await refreshData();
    showToast("Тема сохранена.");
  } catch (error) {
    showFormError("topic-form-error", apiErrorMessage(error));
  }
}

function setupEventListeners() {
  for (const button of document.querySelectorAll("[data-close-dialog]")) {
    button.addEventListener("click", () => button.closest("dialog").close());
  }

  for (const dialog of document.querySelectorAll("dialog")) {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  }

  document.querySelector("#add-subject-button").addEventListener("click", openSubjectDialog);
  document.querySelector("#add-quarter-button").addEventListener("click", openQuarterDialog);
  document.querySelector("#add-topic-top").addEventListener("click", () => openTopicDialog());
  document.querySelector("#add-topic-hero").addEventListener("click", () => openTopicDialog());
  document.querySelector("#refresh-button").addEventListener("click", refreshData);
  document.querySelector("#subject-form").addEventListener("submit", submitSubject);
  document.querySelector("#quarter-form").addEventListener("submit", submitQuarter);
  document.querySelector("#topic-form").addEventListener("submit", submitTopic);

  elements.search.addEventListener("input", renderTopics);
  elements.subjectFilter.addEventListener("change", renderTopics);
  elements.quarterFilter.addEventListener("change", renderTopics);
  elements.statusFilter.addEventListener("change", renderTopics);

  for (const link of document.querySelectorAll(".nav-link")) {
    link.addEventListener("click", () => {
      document.querySelectorAll(".nav-link").forEach((item) => item.classList.remove("is-active"));
      link.classList.add("is-active");
    });
  }
}

setupEventListeners();
refreshData();
