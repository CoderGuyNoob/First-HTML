let scores = [];
let activeCard = null;
let currentValue = 0;
let isDailyDouble = false;
let dailyDoubleWager = 0;
const completed = new Set();

function cardId(category, value) {
  return `${category}__${value}`;
}

function findCard(category, value) {
  return GAME_DATA.cards.find(c => c.category === category && c.value === value);
}

function getPointValue() {
  return isDailyDouble ? dailyDoubleWager : currentValue;
}

// ── Board ──

function buildBoard() {
  const board = document.getElementById("board");
  board.innerHTML = "";

  const cols = GAME_DATA.categories.length;
  board.style.setProperty("--cols", cols);
  document.documentElement.style.setProperty("--cols", cols);

  GAME_DATA.categories.forEach(cat => {
    const div = document.createElement("div");
    div.className = "category";
    div.textContent = cat;
    board.appendChild(div);
  });

  VALUES.forEach(value => {
    GAME_DATA.categories.forEach(category => {
      const card = findCard(category, value);
      const btn = document.createElement("button");
      btn.className = "tile";
      if (!card) {
        btn.className += " empty";
        btn.disabled = true;
      } else {
        btn.id = cardId(category, value);
        btn.textContent = `$${value}`;
        btn.onclick = () => openCard(card);
        if (completed.has(btn.id)) btn.classList.add("used");
      }
      board.appendChild(btn);
    });
  });
}

// ── Scoreboard ──

function buildScoreboard() {
  const section = document.getElementById("scoreboard");
  section.innerHTML = "";
  scores = new Array(TEAM_COUNT).fill(0);

  for (let i = 0; i < TEAM_COUNT; i++) {
    const team = document.createElement("div");
    team.className = "team";
    team.innerHTML = `
      <div class="team-top">
        <input class="team-name" value="Team ${i + 1}" aria-label="Team ${i + 1} name">
      </div>
      <div class="score" id="score${i}">0</div>
      <div class="score-buttons">
        <button class="btn secondary" onclick="changeScore(${i}, -getPointValue())">&minus;</button>
        <button class="btn" onclick="changeScore(${i}, getPointValue())">+</button>
      </div>`;
    section.appendChild(team);
  }
}

// ── Modal ──

function openCard(card) {
  const id = cardId(card.category, card.value);
  if (completed.has(id)) return;

  activeCard = card;
  currentValue = card.value;
  isDailyDouble = !!card.dailyDouble;

  if (isDailyDouble) {
    const maxWager = Math.max(0, ...scores);
    showWagerModal(card.category, maxWager);
  } else {
    showQuestion(card);
  }
}

function showWagerModal(category, maxWager) {
  const modal = document.getElementById("wagerModal");
  document.getElementById("wagerTitle").textContent = "Daily Double!";
  document.getElementById("wagerCategory").textContent = category;
  const input = document.getElementById("wagerInput");
  input.value = "";
  input.max = maxWager;
  document.getElementById("wagerMax").textContent = `Wager up to $${maxWager}`;
  document.getElementById("wagerError").textContent = "";
  modal.classList.add("show");
  setTimeout(() => input.focus(), 100);
}

function confirmWager() {
  const input = document.getElementById("wagerInput");
  const maxWager = parseInt(input.max) || 0;
  const wager = parseInt(input.value) || 0;
  if (wager < 0) {
    document.getElementById("wagerError").textContent = "Wager cannot be negative";
    return;
  }
  if (wager > maxWager) {
    document.getElementById("wagerError").textContent = `Max wager is $${maxWager}`;
    return;
  }
  dailyDoubleWager = wager;
  document.getElementById("wagerModal").classList.remove("show");
  showQuestion(activeCard);
}

function cancelWager() {
  document.getElementById("wagerModal").classList.remove("show");
  activeCard = null;
  isDailyDouble = false;
}

function showQuestion(card) {
  if (isDailyDouble) {
    document.getElementById("modalMeta").textContent = `${card.category} • Daily Double • $${dailyDoubleWager}`;
  } else {
    document.getElementById("modalMeta").textContent = `${card.category} • $${card.value}`;
  }
  document.getElementById("modalQuestion").textContent = card.question;

  const answer = document.getElementById("modalAnswer");
  answer.textContent = card.answer;
  answer.classList.remove("show");

  document.getElementById("modalBackdrop").classList.add("show");
}

function showAnswer() {
  document.getElementById("modalAnswer").classList.add("show");
}

function closeModal() {
  document.getElementById("modalBackdrop").classList.remove("show");
}

function backdropClose(event) {
  if (event.target.id === "modalBackdrop") closeModal();
}

function markCompleteAndClose() {
  if (activeCard) {
    const id = cardId(activeCard.category, activeCard.value);
    completed.add(id);
    document.getElementById(id).classList.add("used");
  }
  closeModal();
}

// ── Scores ──

function changeScore(teamIndex, delta) {
  if (!delta) delta = 0;
  scores[teamIndex] += delta;
  document.getElementById(`score${teamIndex}`).textContent = scores[teamIndex];
}

function resetScores() {
  scores.fill(0);
  scores.forEach((s, i) => {
    document.getElementById(`score${i}`).textContent = s;
  });
}

// ── Reset ──

function resetBoard() {
  completed.clear();
  currentValue = 0;
  activeCard = null;
  isDailyDouble = false;
  dailyDoubleWager = 0;
  buildBoard();
  closeModal();
}

// ── Keyboard shortcuts ──

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeModal();
    cancelWager();
  }
  if (e.key.toLowerCase() === "a") showAnswer();
  if (e.key === "Enter") {
    const wagerModal = document.getElementById("wagerModal");
    if (wagerModal.classList.contains("show")) confirmWager();
  }
});

// ── Init ──

function initGame() {
  buildScoreboard();
  buildBoard();
}
