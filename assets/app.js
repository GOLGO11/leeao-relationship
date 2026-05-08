(function () {
  const data = window.LEEAO_RELATIONSHIP_DATA;
  const state = {
    query: "",
    category: "all",
    confidence: 1,
    selected: null,
    graphView: { x: 0, y: 0, k: 1 },
    pan: null,
    touchPointers: new Map(),
    pinch: null,
  };

  const $ = (id) => document.getElementById(id);
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
    witness: "#64748b",
    publishing: "#7c3aed",
    academic: "#1d4ed8",
    academic_admin: "#4338ca",
    scientist: "#0369a1",
    media: "#0284c7",
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
    politician: "#b45309",
    political_dissident: "#dc2626",
    intelligence_police: "#92400e",
    military_figure: "#7c2d12",
    party_propaganda: "#be123c",
    institutional_security: "#475569",
    underworld: "#525252",
    public_debate: "#ea580c",
    spiritual: "#377a38",
    fictional: "#a21caf",
    nickname: "#64748b",
    mentioned: "#64748b",
  };

  function textIncludes(value, query) {
    return String(value || "").toLowerCase().includes(query);
  }

  function personAliasText(person) {
    return (person.aliases || []).join(" ");
  }

  function identityLinks() {
    if (Array.isArray(data.identityLinks)) return data.identityLinks;
    return data.people.flatMap((person) =>
      (person.categoryStats || []).map((stat) => ({
        person: person.name,
        category: stat.category,
        categoryLabel: stat.label,
        count: stat.count,
        personOccurrences: person.occurrences,
        confidence: person.confidence,
      })),
    );
  }

  function personMatches(person) {
    const categories = person.categories || [person.category];
    if (state.category !== "all" && !categories.includes(state.category)) return false;
    if (person.confidence < state.confidence) return false;
    if (!state.query) return true;
    const query = state.query;
    return (
      textIncludes(person.name, query) ||
      textIncludes(personAliasText(person), query) ||
      textIncludes((person.categoryLabels || [person.categoryLabel]).join(" "), query) ||
      person.cues.some((item) => textIncludes(item.cue, query)) ||
      person.evidence.some((item) => textIncludes(item.snippet, query) || textIncludes(item.chapter, query))
    );
  }

  function personMatchesBase(person) {
    if (person.confidence < state.confidence) return false;
    if (!state.query) return true;
    const query = state.query;
    return (
      textIncludes(person.name, query) ||
      textIncludes(personAliasText(person), query) ||
      textIncludes((person.categoryLabels || [person.categoryLabel]).join(" "), query) ||
      person.cues.some((item) => textIncludes(item.cue, query)) ||
      person.evidence.some((item) => textIncludes(item.snippet, query) || textIncludes(item.chapter, query))
    );
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
    state.graphView = { x: 0, y: 0, k: 1 };
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
    $("bookCount").textContent = `${data.books.length} 本`;
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
    const radius = Math.max(150, Math.min(width, height) * 0.28);

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
      const distance = radius + 75 + (seed % 110);
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

    return { nodes, links: graphLinks, activeCategories, peopleByName };
  }

  function simulate(graph, width, height) {
    const nodes = graph.nodes.filter((node) => !node.fixed);
    for (let tick = 0; tick < 180; tick += 1) {
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
        node.vx *= 0.84;
        node.vy *= 0.84;
        node.x = Math.max(24, Math.min(width - 24, node.x + node.vx));
        node.y = Math.max(24, Math.min(height - 24, node.y + node.vy));
      });
    }
  }

  function renderGraph() {
    const svg = $("graphSvg");
    const width = Math.max(960, svg.clientWidth || 960);
    const height = Math.max(720, svg.clientHeight || 680);
    const filteredPeople = data.people.filter(personMatches);
    $("resultCount").textContent = `${filteredPeople.length.toLocaleString("zh-CN")} 人`;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";
    svg.style.cursor = "grab";

    if (!filteredPeople.length) {
      renderLegend([]);
      renderDetail(null);
      return;
    }

    const graph = buildGraph(filteredPeople, width, height);
    simulate(graph, width, height);
    renderLegend(graph.activeCategories);

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
      line.setAttribute("stroke-width", link.type === "identity" ? Math.max(1, Math.min(5, 1 + (link.link.count || 1) * 0.45)) : "1.2");
      line.setAttribute("class", `graph-link ${link.type}`);
      if (link.type === "identity") line.setAttribute("stroke", categoryColors[link.link.category] || "#64748b");
      linkLayer.appendChild(line);
    });

    graph.nodes.forEach((node) => {
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", `node ${node.type}${state.selected && state.selected.id === node.id ? " selected" : ""}`);
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
        state.selected = node;
        renderDetail(node);
        renderGraph();
      });
      nodeLayer.appendChild(group);
    });

    if (!state.selected) {
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
      $("detailBody").innerHTML = `<div class="metricLine"><span>人物 ${data.totals.people}</span><span>身份边 ${identityLinks().length}</span></div>`;
      return;
    }

    if (node.type === "category") {
      const people = data.people
        .filter((person) => (person.categories || []).includes(node.category))
        .sort((a, b) => b.occurrences - a.occurrences)
        .slice(0, 40);
      $("detailName").textContent = node.name;
      $("detailMeta").textContent = "独立身份分类";
      $("detailBody").innerHTML = `
        <div class="metricLine"><span>${people.length} 人显示</span></div>
        <div class="miniList">
          ${people.map((person) => `<button data-person="${person.name}"><strong>${person.name}</strong><span>${person.occurrences} 次</span></button>`).join("")}
        </div>
      `;
      $("detailBody").querySelectorAll("button[data-person]").forEach((button) => {
        button.addEventListener("click", () => {
          const person = data.people.find((item) => item.name === button.dataset.person);
          if (person) renderDetail({ id: `person:${person.name}`, type: "person", name: person.name, person });
        });
      });
      return;
    }

    const person = node.person;
    $("detailName").textContent = person.name;
    $("detailMeta").textContent = `出现 ${person.occurrences} 次 · 可信度 ${person.confidence}`;
    const identities = (person.categoryStats || []).map((stat) => categoryPill(stat.category, stat.label, stat.count)).join("");
    const aliases = (person.aliases || []).filter(Boolean);
    const aliasLine = aliases.length
      ? `<div class="aliasLine"><strong>别名/外号：</strong>${aliases.map((alias) => `<span>${alias}</span>`).join("")}</div>`
      : "";
    const cues = person.cues.length ? person.cues.map((x) => `${x.cue}(${x.count})`).join("、") : "无明显线索";
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
    $("detailBody").innerHTML = `
      <div class="metricLine">
        <span>出现 ${person.occurrences}</span>
        <span>相关出现 ${person.relevantOccurrences}</span>
        <span>章节 ${person.chapterCount}</span>
      </div>
      <div class="identityList">${identities}</div>
      ${aliasLine}
      <div><strong>线索：</strong>${cues}</div>
      <div class="evidence">${evidence || "暂无证据片段"}</div>
    `;
  }

  function renderBooks() {
    const grid = $("bookGrid");
    grid.innerHTML = "";
    data.books.forEach((book) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "bookItem";
      item.innerHTML = `
        <strong>《${book.book}》</strong>
        <span>${book.collection} · ${book.chapters} 章 · ${book.personCount} 人</span>
        <p>${book.people.slice(0, 8).map((x) => x.name).join("、")}</p>
      `;
      grid.appendChild(item);
    });
  }

  function bindEvents() {
    $("searchInput").addEventListener("input", (event) => {
      state.query = event.target.value.trim().toLowerCase();
      state.selected = null;
      state.graphView = { x: 0, y: 0, k: 1 };
      renderGraph();
    });
    $("categoryFilter").addEventListener("change", (event) => {
      setCategory(event.target.value);
    });
    $("confidenceFilter").addEventListener("input", (event) => {
      state.confidence = Number(event.target.value);
      $("confidenceValue").textContent = state.confidence;
      state.selected = null;
      state.graphView = { x: 0, y: 0, k: 1 };
      renderGraph();
    });
    window.addEventListener("resize", () => {
      state.selected = null;
      state.graphView = { x: 0, y: 0, k: 1 };
      renderGraph();
    });
    bindGraphInteractions();
  }

  if (!data) {
    document.body.innerHTML = '<main class="layout">尚未生成数据，请先运行 scripts/extract_relationships.py。</main>';
    return;
  }

  fillFilters();
  fillStats();
  renderBooks();
  bindEvents();
  renderGraph();
})();
