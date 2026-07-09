(function () {
  const data = window.LEEAO_RELATIONSHIP_DATA;
  const state = {
    query: "",
    category: "all",
    confidence: 1,
    selected: null,
    lockedPersonName: "",
    nameInitial: "",
    graphView: { x: 0, y: 0, k: 1 },
    pan: null,
    touchPointers: new Map(),
    pinch: null,
  };

  const $ = (id) => document.getElementById(id);
  const DEFAULT_GRAPH_NODE_LIMIT = 240;
  const FILTERED_GRAPH_NODE_LIMIT = 420;
  const SEARCH_RENDER_DELAY = 140;
  const NAME_INITIALS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ#".split("");
  const pinyinCollator = new Intl.Collator("zh-CN-u-co-pinyin", { numeric: true, sensitivity: "base" });
  const pinyinBoundaries = [
    ["A", "阿"],
    ["B", "八"],
    ["C", "嚓"],
    ["D", "哒"],
    ["E", "娥"],
    ["F", "发"],
    ["G", "旮"],
    ["H", "哈"],
    ["J", "击"],
    ["K", "喀"],
    ["L", "垃"],
    ["M", "妈"],
    ["N", "拿"],
    ["O", "哦"],
    ["P", "啪"],
    ["Q", "期"],
    ["R", "然"],
    ["S", "撒"],
    ["T", "塌"],
    ["W", "挖"],
    ["X", "昔"],
    ["Y", "压"],
    ["Z", "匝"],
  ];
  let renderTimer = null;

  if (!data) {
    document.body.innerHTML = '<main class="layout">尚未生成数据，请先运行 scripts/extract_relationships.py。</main>';
    return;
  }

  const categoryColors = {
    meeting: "#0f766e",
    correspondence: "#0891b2",
    neighbor: "#15803d",
    teacher_student: "#2563eb",
    classmate: "#4f46e5",
    colleague: "#0f766e",
    editor: "#9333ea",
    friendship: "#14b8a6",
    martyr: "#b91c1c",
    family: "#be3455",
    in_law: "#db2777",
    marriage_context: "#ea580c",
    romance: "#e11d48",
    property_finance: "#a16207",
    trust_property: "#ca8a04",
    public_funds: "#d97706",
    torture_victim: "#c2410c",
    torture_actor: "#7f1d1d",
    victim: "#be123c",
    witness: "#64748b",
    publishing: "#7c3aed",
    source_author: "#0d9488",
    academic: "#1d4ed8",
    academic_admin: "#4338ca",
    scientist: "#0369a1",
    media: "#0284c7",
    public_official: "#64748b",
    campaign_election: "#16a34a",
    household_staff: "#65a30d",
    disability: "#0d9488",
    human_rights: "#059669",
    veteran: "#475569",
    social_case: "#991b1b",
    anti_communist_defector: "#475569",
    medical_care: "#0e7490",
    religion: "#7c3aed",
    indoctrination: "#9f1239",
    legal_official: "#6d5bd0",
    lawyer_counsel: "#8b5cf6",
    prison_admin: "#334155",
    prison_guard: "#78716c",
    prison_medical: "#0f766e",
    litigation: "#9333ea",
    case_prison: "#475569",
    source_support: "#0891b2",
    research_reference: "#0369a1",
    politician: "#b45309",
    political_dissident: "#dc2626",
    intelligence_police: "#92400e",
    military_figure: "#7c2d12",
    party_propaganda: "#be123c",
    institutional_security: "#475569",
    underworld: "#525252",
    public_debate: "#ea580c",
    plot_character: "#be123c",
    literary_character: "#7e22ce",
    historical_allusion: "#64748b",
    spiritual: "#377a38",
    fictional: "#a21caf",
    nickname: "#64748b",
    mentioned: "#64748b",
  };

  function normalizeSearch(value) {
    return String(value || "")
      .trim()
      .toLocaleLowerCase("zh-CN")
      .replace(/\s+/g, "");
  }

  function makeSearchText(parts) {
    return normalizeSearch(parts.filter(Boolean).join(" "));
  }

  function personSortInitial(name) {
    const first = String(name || "").trim().charAt(0);
    if (!first) return "#";
    if (/^[a-z]$/i.test(first)) return first.toUpperCase();
    if (!/[\u4e00-\u9fff]/.test(first)) return "#";

    let initial = "#";
    pinyinBoundaries.forEach(([letter, boundary]) => {
      if (pinyinCollator.compare(first, boundary) >= 0) initial = letter;
    });
    return initial;
  }

  function comparePeopleName(a, b) {
    return pinyinCollator.compare(a.name, b.name) || a.name.localeCompare(b.name, "zh-CN");
  }

  data.people.forEach((person) => {
    const categories = person.categories || [person.category];
    person.aliases = person.aliases || [];
    person.category = person.category || categories[0];
    person.primaryCategory = person.primaryCategory || person.category;
    person.categoryLabel = person.categoryLabel || data.categoryLabels[person.category] || person.category;
    person.primaryCategoryLabel = person.primaryCategoryLabel || data.categoryLabels[person.primaryCategory] || person.primaryCategory;
    person.categoryLabels = person.categoryLabels || categories.map((category) => data.categoryLabels[category] || category);
    person.categoryStats = (person.categoryStats || categories.map((category) => ({ category, count: 1 }))).map((stat) => ({
      ...stat,
      label: stat.label || data.categoryLabels[stat.category] || stat.category,
    }));
    person.cues = person.cues || [];
    person.evidence = person.evidence || [];
    const identitySearchText = makeSearchText([
      (person.categoryLabels || [person.categoryLabel]).join(" "),
      person.cues.map((item) => item.cue).join(" "),
    ]);
    const evidenceSearchText = makeSearchText(
      person.evidence.map((item) => `${item.book || ""} ${item.chapter || ""} ${item.snippet || ""}`),
    );
    person.search = {
      name: normalizeSearch(person.name),
      aliases: person.aliases.map(normalizeSearch).filter(Boolean),
      identity: identitySearchText,
      evidence: evidenceSearchText,
    };
    person.search.all = [person.search.name, ...person.search.aliases, person.search.identity, person.search.evidence].join("");
    person.searchText = person.search.all;
    person.sortInitial = personSortInitial(person.name);
  });

  const personIndex = new Map(data.people.map((person) => [person.name, person]));
  const identityLinkRows = Array.isArray(data.identityLinks)
    ? data.identityLinks
    : data.people.flatMap((person) =>
      (person.categoryStats || []).map((stat) => ({
        person: person.name,
        category: stat.category,
        categoryLabel: stat.label,
        count: stat.count,
        personOccurrences: person.occurrences,
        confidence: person.confidence,
      })),
    );
  const personRelationRows = Array.isArray(data.personRelations) ? data.personRelations : [];
  const searchNameIndex = new Map();
  const relationNeighborsByName = new Map();
  const peopleByInitial = new Map(NAME_INITIALS.map((initial) => [initial, []]));
  let exactNameCache = { query: null, names: new Set() };

  function addSearchName(key, person) {
    if (!key) return;
    if (!searchNameIndex.has(key)) searchNameIndex.set(key, []);
    searchNameIndex.get(key).push(person);
  }

  function addRelationNeighbor(source, target) {
    if (!source || !target) return;
    if (!relationNeighborsByName.has(source)) relationNeighborsByName.set(source, new Set());
    relationNeighborsByName.get(source).add(target);
  }

  data.people.forEach((person) => {
    addSearchName(person.search.name, person);
    person.search.aliases.forEach((alias) => addSearchName(alias, person));
    const initial = peopleByInitial.has(person.sortInitial) ? person.sortInitial : "#";
    peopleByInitial.get(initial).push(person);
  });

  NAME_INITIALS.forEach((initial) => {
    peopleByInitial.get(initial).sort(comparePeopleName);
  });
  state.nameInitial = NAME_INITIALS.find((initial) => peopleByInitial.get(initial).length) || "#";

  personRelationRows.forEach((relation) => {
    addRelationNeighbor(relation.source, relation.target);
    addRelationNeighbor(relation.target, relation.source);
  });

  function identityLinks() {
    return identityLinkRows;
  }

  function personRelations() {
    return personRelationRows;
  }

  function exactNamesForQuery(query = state.query) {
    if (exactNameCache.query === query) return exactNameCache.names;
    const exactPeople = query ? searchNameIndex.get(query) || [] : [];
    exactNameCache = { query, names: new Set(exactPeople.map((person) => person.name)) };
    return exactNameCache.names;
  }

  function isRelatedToAny(name, names) {
    const neighbors = relationNeighborsByName.get(name);
    if (!neighbors) return false;
    return [...names].some((exactName) => neighbors.has(exactName));
  }

  function searchScore(person, query = state.query) {
    if (!query) return 0;
    if (person.search.name === query) return 1000;
    if (person.search.aliases.some((alias) => alias === query)) return 960;
    if (person.search.name.startsWith(query)) return 920;
    if (person.search.aliases.some((alias) => alias.startsWith(query))) return 880;
    if (person.search.name.includes(query)) return 820;
    if (person.search.aliases.some((alias) => alias.includes(query))) return 780;
    if (person.search.identity.includes(query)) return 420;
    if (person.search.evidence.includes(query)) return 120;
    return 0;
  }

  function personPassesCategory(person) {
    const categories = person.categories || [person.category];
    return state.category === "all" || categories.includes(state.category);
  }

  function makePersonSelection(person) {
    return { id: `person:${person.name}`, type: "person", name: person.name, person };
  }

  function personMatches(person) {
    const exactNames = exactNamesForQuery();
    if (exactNames.size) {
      if (exactNames.has(person.name)) return true;
      if (person.confidence < state.confidence || !personPassesCategory(person)) return false;
      return isRelatedToAny(person.name, exactNames);
    }

    if (!personPassesCategory(person)) return false;
    if (person.confidence < state.confidence) return false;
    if (!state.query) return true;
    return searchScore(person) > 0;
  }

  function personMatchesBase(person) {
    const exactNames = exactNamesForQuery();
    if (exactNames.size) {
      if (exactNames.has(person.name)) return true;
      if (person.confidence < state.confidence) return false;
      return isRelatedToAny(person.name, exactNames);
    }

    if (person.confidence < state.confidence) return false;
    if (!state.query) return true;
    return searchScore(person) > 0;
  }

  function availableCategories() {
    const peopleByName = new Set(data.people.filter(personMatchesBase).map((person) => person.name));
    return [...new Set(identityLinks().filter((link) => peopleByName.has(link.person)).map((link) => link.category))];
  }

  function setCategory(category) {
    state.category = category;
    const filter = $("categoryFilter");
    if (filter) filter.value = category;
    state.selected = null;
    state.lockedPersonName = "";
    state.graphView = { x: 0, y: 0, k: 1 };
    renderNameIndex();
    renderGraph();
  }

  function fillFilters() {
    const categoryFilter = $("categoryFilter");
    categoryFilter.innerHTML = '<option value="all">全部身份</option>';
    Object.entries(data.categoryLabels).forEach(([key, label]) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = label;
      categoryFilter.appendChild(option);
    });
  }

  function fillStats() {
    $("statPeople").textContent = data.totals.people.toLocaleString("zh-CN");
    $("statIdentities").textContent = identityLinks().length.toLocaleString("zh-CN");
    $("statBooks").textContent = data.totals.books.toLocaleString("zh-CN");
    $("statChapters").textContent = data.totals.chapters.toLocaleString("zh-CN");
  }

  function categoryPill(category, label, count) {
    const color = categoryColors[category] || "#64748b";
    const suffix = count ? ` ${count}` : "";
    return `<span class="identityPill"><i style="background:${color}"></i>${label}${suffix}</span>`;
  }

  function renderLegend(activeCategories) {
    const categories = availableCategories();
    const currentCategories = new Set(activeCategories);
    $("legend").innerHTML = categories
      .map((category) => {
        const label = data.categoryLabels[category] || category;
        const color = categoryColors[category] || "#64748b";
        const isSelected = state.category === category;
        const isVisible = currentCategories.has(category);
        return `<button type="button" data-category="${category}" class="${isSelected ? "active" : ""}${isVisible ? "" : " muted"}" title="只显示${label}"><i style="background:${color}"></i>${label}</button>`;
      })
      .join("");
    $("legend").querySelectorAll("button[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        setCategory(button.dataset.category);
      });
    });
  }

  function hashName(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i += 1) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    return hash;
  }

  function buildGraph(filteredPeople, width, height) {
    const peopleByName = new Map(filteredPeople.map((person) => [person.name, person]));
    const links = identityLinks().filter((link) => peopleByName.has(link.person));
    const activeCategories = [...new Set(links.map((link) => link.category))];
    const center = { id: "center:leeao", type: "center", name: "李敖", x: width / 2, y: height / 2, fixed: true, r: 28 };
    const nodes = [center];
    const categoryNodes = new Map();
    const personNodes = new Map();
    const radius = Math.max(180, Math.min(width * 0.33, height * 0.36));

    activeCategories.forEach((category, index) => {
      const angle = (-Math.PI / 2) + (index / Math.max(activeCategories.length, 1)) * Math.PI * 2;
      const node = {
        id: `category:${category}`,
        type: "category",
        category,
        name: data.categoryLabels[category] || category,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        fixed: true,
        r: 18,
      };
      categoryNodes.set(category, node);
      nodes.push(node);
    });

    filteredPeople.forEach((person) => {
      const seed = hashName(person.name);
      const angle = (seed % 628) / 100;
      const distance = radius + 95 + (seed % 130);
      const node = {
        id: `person:${person.name}`,
        type: "person",
        name: person.name,
        person,
        x: width / 2 + Math.cos(angle) * distance,
        y: height / 2 + Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        r: Math.max(6, Math.min(20, 5 + Math.sqrt(person.occurrences))),
      };
      personNodes.set(person.name, node);
      nodes.push(node);
    });

    const graphLinks = [];
    filteredPeople.forEach((person) => {
      graphLinks.push({
        source: center,
        target: personNodes.get(person.name),
        type: "person",
        strength: 0.015,
        length: 210 + Math.min(person.occurrences, 60),
      });
    });
    links.forEach((link) => {
      const categoryNode = categoryNodes.get(link.category);
      const personNode = personNodes.get(link.person);
      if (!categoryNode || !personNode) return;
      graphLinks.push({
        source: categoryNode,
        target: personNode,
        type: "identity",
        link,
        strength: 0.035,
        length: 90 + Math.max(0, 12 - link.count) * 5,
      });
    });
    personRelations().forEach((relation) => {
      const sourceNode = personNodes.get(relation.source);
      const targetNode = personNodes.get(relation.target);
      if (!sourceNode || !targetNode) return;
      graphLinks.push({
        source: sourceNode,
        target: targetNode,
        type: "relation",
        relation,
        strength: 0.028,
        length: 115 + Math.max(0, 10 - (relation.weight || 1)) * 8,
      });
    });

    return { nodes, links: graphLinks, activeCategories, peopleByName };
  }

  function graphNodeLimit() {
    return state.query || state.category !== "all" ? FILTERED_GRAPH_NODE_LIMIT : DEFAULT_GRAPH_NODE_LIMIT;
  }

  function rankPeopleForGraph(people) {
    const selectedName = state.selected && state.selected.type === "person" ? state.selected.name : "";
    const lockedName = state.lockedPersonName;
    return [...people].sort((a, b) => {
      if (lockedName && a.name === lockedName) return -1;
      if (lockedName && b.name === lockedName) return 1;
      if (a.name === selectedName) return -1;
      if (b.name === selectedName) return 1;
      if (state.query) {
        const scoreDiff = searchScore(b) - searchScore(a);
        if (scoreDiff) return scoreDiff;
      }
      return (b.confidence - a.confidence) || (b.relevantOccurrences - a.relevantOccurrences) || (b.occurrences - a.occurrences) || a.name.localeCompare(b.name, "zh-CN");
    });
  }

  function visiblePeopleForGraph(filteredPeople) {
    const limit = graphNodeLimit();
    if (!state.query && !state.lockedPersonName && filteredPeople.length <= limit) return filteredPeople;
    return rankPeopleForGraph(filteredPeople).slice(0, limit);
  }

  function simulate(graph, width, height) {
    const nodes = graph.nodes.filter((node) => !node.fixed);
    const tickCount = nodes.length > 320 ? 72 : nodes.length > 220 ? 96 : 132;
    const softLimitX = Math.max(260, width * 0.34);
    const softLimitY = Math.max(220, height * 0.36);
    for (let tick = 0; tick < tickCount; tick += 1) {
      graph.links.forEach((link) => {
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (distance - link.length) * link.strength;
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        if (!link.source.fixed) {
          link.source.vx = (link.source.vx || 0) + fx;
          link.source.vy = (link.source.vy || 0) + fy;
        }
        if (!link.target.fixed) {
          link.target.vx = (link.target.vx || 0) - fx;
          link.target.vy = (link.target.vy || 0) - fy;
        }
      });

      for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const distance2 = Math.max(dx * dx + dy * dy, 80);
          const distance = Math.sqrt(distance2);
          const force = Math.min(1.8, 900 / distance2);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }

      nodes.forEach((node) => {
        node.vx += (width / 2 - node.x) * 0.0012;
        node.vy += (height / 2 - node.y) * 0.0012;
        if (node.x < -softLimitX) node.vx += (-softLimitX - node.x) * 0.004;
        if (node.x > width + softLimitX) node.vx += (width + softLimitX - node.x) * 0.004;
        if (node.y < -softLimitY) node.vy += (-softLimitY - node.y) * 0.004;
        if (node.y > height + softLimitY) node.vy += (height + softLimitY - node.y) * 0.004;
        node.vx *= 0.84;
        node.vy *= 0.84;
        node.x += node.vx;
        node.y += node.vy;
      });
    }
  }

  function fitGraphView(graph, width, height) {
    const visibleNodes = graph.nodes.filter((node) => node.type !== "center");
    if (!visibleNodes.length) return { x: 0, y: 0, k: 1 };
    const padding = 56;
    const bounds = visibleNodes.reduce((box, node) => ({
      minX: Math.min(box.minX, node.x - node.r),
      maxX: Math.max(box.maxX, node.x + node.r + Math.min(node.name.length * 12, 96)),
      minY: Math.min(box.minY, node.y - node.r - 10),
      maxY: Math.max(box.maxY, node.y + node.r + 10),
    }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });
    const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
    const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
    const minScale = visibleNodes.length > 320 ? 0.48 : visibleNodes.length > 220 ? 0.58 : 0.72;
    const scale = Math.max(minScale, Math.min(1.35, Math.min(
      (width - padding * 2) / graphWidth,
      (height - padding * 2) / graphHeight,
    )));
    return {
      x: (width - graphWidth * scale) / 2 - bounds.minX * scale,
      y: (height - graphHeight * scale) / 2 - bounds.minY * scale,
      k: scale,
    };
  }

  function syncDetailPaneHeight() {
    const layout = document.querySelector(".networkLayout");
    const graphPane = document.querySelector(".graphPane");
    if (!layout || !graphPane || window.matchMedia("(max-width: 980px)").matches) {
      if (layout) layout.style.removeProperty("--detail-pane-height");
      return;
    }
    layout.style.setProperty("--detail-pane-height", `${Math.ceil(graphPane.offsetHeight)}px`);
  }

  function lockPerson(name, { syncSearch = true } = {}) {
    const person = personIndex.get(name);
    if (!person) return;

    state.lockedPersonName = person.name;
    state.nameInitial = peopleByInitial.has(person.sortInitial) ? person.sortInitial : "#";
    state.selected = makePersonSelection(person);
    state.category = "all";
    const categoryFilter = $("categoryFilter");
    if (categoryFilter) categoryFilter.value = "all";
    if (syncSearch) {
      state.query = normalizeSearch(person.name);
      const searchInput = $("searchInput");
      if (searchInput) searchInput.value = person.name;
    }
    state.graphView = { x: 0, y: 0, k: 1 };
    renderNameIndex();
    renderGraph();
  }

  function clearPersonLock() {
    state.lockedPersonName = "";
    renderNameIndex();
    renderGraph();
  }

  function ensureSelectedPerson(filteredPeople) {
    if (!filteredPeople.length) {
      state.selected = null;
      return;
    }

    const visibleNames = new Set(filteredPeople.map((person) => person.name));
    if (state.lockedPersonName && visibleNames.has(state.lockedPersonName)) {
      state.selected = makePersonSelection(personIndex.get(state.lockedPersonName));
      return;
    }
    if (state.selected && state.selected.type === "person" && visibleNames.has(state.selected.name)) return;
    if (state.query) {
      state.selected = makePersonSelection(rankPeopleForGraph(filteredPeople)[0]);
      return;
    }
    state.selected = null;
  }

  function renderNameIndex() {
    const letters = $("nameIndexLetters");
    const list = $("nameIndexList");
    const meta = $("nameIndexMeta");
    if (!letters || !list || !meta) return;

    letters.innerHTML = "";
    NAME_INITIALS.forEach((initial) => {
      const people = peopleByInitial.get(initial) || [];
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `${initial} ${people.length}`;
      button.disabled = !people.length;
      button.className = state.nameInitial === initial ? "active" : "";
      button.addEventListener("click", () => {
        state.nameInitial = initial;
        renderNameIndex();
      });
      letters.appendChild(button);
    });

    const people = peopleByInitial.get(state.nameInitial) || [];
    meta.textContent = state.lockedPersonName
      ? `已锁定：${state.lockedPersonName}`
      : `${state.nameInitial} 组 ${people.length.toLocaleString("zh-CN")} 人`;

    list.innerHTML = "";
    if (state.lockedPersonName) {
      const lockBar = document.createElement("div");
      lockBar.className = "lockBar";
      const label = document.createElement("span");
      label.textContent = `当前锁定 ${state.lockedPersonName}`;
      const clearButton = document.createElement("button");
      clearButton.type = "button";
      clearButton.textContent = "解除";
      clearButton.addEventListener("click", clearPersonLock);
      lockBar.append(label, clearButton);
      list.appendChild(lockBar);
    }

    const grid = document.createElement("div");
    grid.className = "nameIndexGrid";
    people.forEach((person) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `nameIndexItem${state.lockedPersonName === person.name ? " locked" : ""}`;
      const name = document.createElement("strong");
      name.textContent = person.name;
      const metaText = document.createElement("span");
      metaText.textContent = `${person.occurrences} 次 · ${person.primaryCategoryLabel}`;
      button.append(name, metaText);
      button.addEventListener("click", () => lockPerson(person.name));
      grid.appendChild(button);
    });
    list.appendChild(grid);
  }

  function renderGraph() {
    const svg = $("graphSvg");
    const width = Math.max(960, svg.clientWidth || 960);
    const height = Math.max(720, svg.clientHeight || 680);
    const filteredPeople = data.people.filter(personMatches);
    ensureSelectedPerson(filteredPeople);
    const graphPeople = visiblePeopleForGraph(filteredPeople);
    $("resultCount").textContent = graphPeople.length < filteredPeople.length
      ? `显示 ${graphPeople.length.toLocaleString("zh-CN")} / 共 ${filteredPeople.length.toLocaleString("zh-CN")} 人`
      : `${filteredPeople.length.toLocaleString("zh-CN")} 人`;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";
    svg.style.cursor = "grab";

    if (!filteredPeople.length) {
      renderLegend([]);
      renderDetail(null);
      return;
    }

    const graph = buildGraph(graphPeople, width, height);
    simulate(graph, width, height);
    state.graphView = fitGraphView(graph, width, height);
    renderLegend(graph.activeCategories);
    syncDetailPaneHeight();

    const viewportLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const linkLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    viewportLayer.setAttribute("class", "graphViewport");
    svg.appendChild(viewportLayer);
    viewportLayer.appendChild(linkLayer);
    viewportLayer.appendChild(nodeLayer);
    applyGraphView(svg, viewportLayer);

    graph.links.forEach((link) => {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", link.source.x);
      line.setAttribute("y1", link.source.y);
      line.setAttribute("x2", link.target.x);
      line.setAttribute("y2", link.target.y);
      line.setAttribute(
        "stroke-width",
        link.type === "identity"
          ? Math.max(1, Math.min(5, 1 + (link.link.count || 1) * 0.45))
          : link.type === "relation"
            ? Math.max(1.2, Math.min(4, 1 + (link.relation.weight || 1) * 0.22))
            : "1.2",
      );
      line.setAttribute("class", `graph-link ${link.type}`);
      if (link.type === "identity") line.setAttribute("stroke", categoryColors[link.link.category] || "#64748b");
      if (link.type === "relation") {
        line.setAttribute("stroke", "#172126");
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${link.relation.source} - ${link.relation.relation} - ${link.relation.target}`;
        line.appendChild(title);
      }
      linkLayer.appendChild(line);
    });

    graph.nodes.forEach((node) => {
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const isSelected = state.selected && state.selected.id === node.id;
      const isLocked = state.lockedPersonName && node.type === "person" && node.name === state.lockedPersonName;
      group.setAttribute("class", `node ${node.type}${isSelected ? " selected" : ""}${isLocked ? " locked" : ""}`);
      group.setAttribute("transform", `translate(${node.x},${node.y})`);
      group.style.cursor = "pointer";

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("r", node.r);
      circle.setAttribute("fill", node.type === "center" ? "#111827" : node.type === "category" ? (categoryColors[node.category] || "#64748b") : "#ffffff");
      if (node.type === "person") {
        const primary = (node.person.categories || [node.person.category])[0];
        circle.setAttribute("fill", categoryColors[primary] || "#64748b");
        circle.setAttribute("fill-opacity", "0.9");
      }
      group.appendChild(circle);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", node.r + 5);
      text.setAttribute("y", "4");
      text.textContent = node.name;
      group.appendChild(text);

      group.addEventListener("click", () => {
        if (node.type === "person") {
          lockPerson(node.name);
          return;
        }
        state.selected = node;
        state.lockedPersonName = "";
        renderDetail(node);
        renderNameIndex();
        svg.querySelectorAll(".node.selected").forEach((item) => item.classList.remove("selected"));
        svg.querySelectorAll(".node.locked").forEach((item) => item.classList.remove("locked"));
        group.classList.add("selected");
        if (node.type === "person") group.classList.add("locked");
      });
      nodeLayer.appendChild(group);
    });

    const selectedNode = state.selected ? graph.nodes.find((node) => node.id === state.selected.id) : null;
    if (selectedNode) {
      state.selected = selectedNode;
      renderDetail(selectedNode);
    } else if (!state.selected) {
      const first = graph.nodes.find((node) => node.type === "person");
      if (first) {
        state.selected = first;
        renderDetail(first);
      }
    }
  }

  function applyGraphView(svg, viewportLayer = svg.querySelector(".graphViewport")) {
    if (!viewportLayer) return;
    const { x, y, k } = state.graphView;
    viewportLayer.setAttribute("transform", `translate(${x} ${y}) scale(${k})`);
  }

  function bindGraphInteractions() {
    const svg = $("graphSvg");

    function pointerDistance(a, b) {
      return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) || 1;
    }

    function pointerCenter(a, b) {
      return {
        x: (a.clientX + b.clientX) / 2,
        y: (a.clientY + b.clientY) / 2,
      };
    }

    function zoomAt(clientX, clientY, nextK) {
      const rect = svg.getBoundingClientRect();
      const pointX = clientX - rect.left;
      const pointY = clientY - rect.top;
      const oldK = state.graphView.k;
      const worldX = (pointX - state.graphView.x) / oldK;
      const worldY = (pointY - state.graphView.y) / oldK;
      state.graphView.k = Math.max(0.55, Math.min(2.8, nextK));
      state.graphView.x = pointX - worldX * state.graphView.k;
      state.graphView.y = pointY - worldY * state.graphView.k;
      applyGraphView(svg);
    }

    svg.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "touch") {
        state.touchPointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY });
        svg.setPointerCapture(event.pointerId);
        if (state.touchPointers.size === 2) {
          const [first, second] = [...state.touchPointers.values()];
          state.pinch = {
            startDistance: pointerDistance(first, second),
            startK: state.graphView.k,
          };
          state.pan = null;
          svg.style.cursor = "grabbing";
          return;
        }
      }
      if (event.button !== 0 || event.target.closest(".node")) return;
      state.pan = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        viewX: state.graphView.x,
        viewY: state.graphView.y,
      };
      svg.setPointerCapture(event.pointerId);
      svg.style.cursor = "grabbing";
    });

    svg.addEventListener("pointermove", (event) => {
      if (state.touchPointers.has(event.pointerId)) {
        state.touchPointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY });
        if (state.pinch && state.touchPointers.size >= 2) {
          const [first, second] = [...state.touchPointers.values()];
          const center = pointerCenter(first, second);
          const ratio = pointerDistance(first, second) / state.pinch.startDistance;
          zoomAt(center.x, center.y, state.pinch.startK * ratio);
          return;
        }
      }
      if (!state.pan || state.pan.pointerId !== event.pointerId) return;
      state.graphView.x = state.pan.viewX + event.clientX - state.pan.startX;
      state.graphView.y = state.pan.viewY + event.clientY - state.pan.startY;
      applyGraphView(svg);
    });

    svg.addEventListener("pointerup", (event) => {
      state.touchPointers.delete(event.pointerId);
      if (state.touchPointers.size < 2) state.pinch = null;
      if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
      if (!state.pan || state.pan.pointerId !== event.pointerId) return;
      state.pan = null;
      svg.style.cursor = "grab";
    });

    svg.addEventListener("pointercancel", (event) => {
      state.touchPointers.delete(event.pointerId);
      state.pinch = null;
      state.pan = null;
      if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
      svg.style.cursor = "grab";
    });

    svg.addEventListener("wheel", (event) => {
      event.preventDefault();
      const scale = event.deltaY < 0 ? 1.12 : 0.9;
      zoomAt(event.clientX, event.clientY, state.graphView.k * scale);
    }, { passive: false });

    svg.addEventListener("dblclick", (event) => {
      if (event.target.closest(".node")) return;
      state.graphView = { x: 0, y: 0, k: 1 };
      applyGraphView(svg);
    });
  }

  function renderDetail(node) {
    if (!node) {
      $("detailName").textContent = "没有匹配节点";
      $("detailMeta").textContent = "调整筛选条件";
      $("detailBody").textContent = "当前筛选没有找到人物。";
      return;
    }

    if (node.type === "center") {
      $("detailName").textContent = "李敖";
      $("detailMeta").textContent = "关系网络中心";
      $("detailBody").innerHTML = `<div class="metricLine"><span>人物 ${data.totals.people}</span><span>身份边 ${identityLinks().length}</span><span>人物关系边 ${personRelations().length}</span></div>`;
      return;
    }

    if (node.type === "category") {
      const allPeople = data.people
        .filter((person) => (person.categories || []).includes(node.category))
        .sort((a, b) => b.occurrences - a.occurrences);
      const people = allPeople.slice(0, 40);
      $("detailName").textContent = node.name;
      $("detailMeta").textContent = "独立身份分类";
      $("detailBody").innerHTML = `
        <div class="metricLine"><span>共 ${allPeople.length} 人</span><span>显示前 ${people.length} 人</span></div>
        <div class="miniList categoryPeopleList">
          ${people.map((person) => `<button data-person="${person.name}"><strong>${person.name}</strong><span>${person.occurrences} 次</span></button>`).join("")}
        </div>
      `;
      $("detailBody").querySelectorAll("button[data-person]").forEach((button) => {
        button.addEventListener("click", () => {
          lockPerson(button.dataset.person);
        });
      });
      return;
    }

    const person = node.person;
    $("detailName").textContent = person.name;
    $("detailMeta").textContent = `${state.lockedPersonName === person.name ? "已锁定 · " : ""}出现 ${person.occurrences} 次 · 可信度 ${person.confidence}`;
    const identities = (person.categoryStats || []).map((stat) => categoryPill(stat.category, stat.label, stat.count)).join("");
    const aliases = (person.aliases || []).filter(Boolean);
    const aliasLine = aliases.length
      ? `<div class="aliasLine"><strong>别名/外号：</strong>${aliases.map((alias) => `<span>${alias}</span>`).join("")}</div>`
      : "";
    const cues = person.cues.length ? person.cues.map((x) => `${x.cue}(${x.count})`).join("、") : "无明显线索";
    const relationItems = personRelations()
      .filter((relation) => relation.source === person.name || relation.target === person.name)
      .map((relation) => {
        const other = relation.source === person.name ? relation.target : relation.source;
        return `
          <article>
            <h3>${relation.relation}：${other}</h3>
            <p>《${relation.book}》：${relation.note}</p>
          </article>
        `;
      })
      .join("");
    const evidence = person.evidence
      .map(
        (ev) => `
          <article>
            <h3>《${ev.book}》 / ${ev.chapter}</h3>
            <p>${ev.snippet}</p>
          </article>
        `,
      )
      .join("");
    const detailActions = state.lockedPersonName === person.name
      ? ""
      : `
      <div class="detailActions">
        <button type="button" data-lock-current>锁定人物</button>
      </div>`;
    $("detailBody").innerHTML = `
      <div class="metricLine">
        <span>出现 ${person.occurrences}</span>
        <span>相关出现 ${person.relevantOccurrences}</span>
        <span>章节 ${person.chapterCount}</span>
      </div>
      ${detailActions}
      <div class="identityList">${identities}</div>
      ${aliasLine}
      <div><strong>线索：</strong>${cues}</div>
      ${relationItems ? `<div class="relationList">${relationItems}</div>` : ""}
      <div class="evidence">${evidence || "暂无证据片段"}</div>
    `;
    $("detailBody").querySelectorAll("button[data-lock-current]").forEach((button) => {
      button.addEventListener("click", () => lockPerson(person.name));
    });
  }

  function bindEvents() {
    function scheduleRender(delay = SEARCH_RENDER_DELAY) {
      window.clearTimeout(renderTimer);
      renderTimer = window.setTimeout(renderGraph, delay);
    }

    $("searchInput").addEventListener("input", (event) => {
      state.query = normalizeSearch(event.target.value);
      state.selected = null;
      state.lockedPersonName = "";
      state.graphView = { x: 0, y: 0, k: 1 };
      renderNameIndex();
      scheduleRender();
    });
    $("categoryFilter").addEventListener("change", (event) => {
      setCategory(event.target.value);
    });
    $("confidenceFilter").addEventListener("input", (event) => {
      state.confidence = Number(event.target.value);
      $("confidenceValue").textContent = state.confidence;
      state.selected = null;
      state.lockedPersonName = "";
      state.graphView = { x: 0, y: 0, k: 1 };
      renderNameIndex();
      scheduleRender();
    });
    window.addEventListener("resize", () => {
      if (!state.lockedPersonName) state.selected = null;
      state.graphView = { x: 0, y: 0, k: 1 };
      scheduleRender(180);
    });
    bindGraphInteractions();
  }

  fillFilters();
  fillStats();
  renderNameIndex();
  bindEvents();
  renderGraph();
})();
