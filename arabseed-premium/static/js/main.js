/**
 * Cinemana Premium - Premium Web Portal JS Controller
 * --------------------------------------------------
 * Manages SPA routing, API communications, dynamic DOM rendering,
 * horizontal category carousel rows, search results grids, and Plyr.js streaming.
 */

// Global App State
const state = {
    activePlayer: null,
    searchResults: [],
    categories: [],
    selectedItem: null,
    currentEpisodes: [],
    activeServerList: [],
    bestServer: null,
    networkType: 'مباشر'
};

// SVG Poster Fallback Data URL
const SVG_POSTER_PLACEHOLDER = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450"><rect width="100%" height="100%" fill="%2314171c"/><g transform="translate(100, 160)"><circle cx="50" cy="50" r="40" fill="%23e50914" opacity="0.15"/><path d="M10 20 L90 20 L80 90 L20 90 Z" fill="%23e50914" opacity="0.6"/><rect x="15" y="30" width="70" height="50" rx="4" fill="%23ef4444" opacity="0.8"/><polygon points="45,45 65,55 45,65" fill="%23ffffff"/><circle cx="50" cy="110" r="8" fill="%2310b981"/><circle cx="20" cy="110" r="6" fill="%23f59e0b"/><circle cx="80" cy="110" r="6" fill="%23f43f5e"/></g><text x="50%" y="360" font-family="'Cairo', sans-serif" font-weight="700" font-size="16" fill="%239ca3af" text-anchor="middle">لا يتوفر بوستر</text></svg>`;

// DOM Elements Cache
const elements = {
    searchForm: document.getElementById('main-search-form'),
    searchInput: document.getElementById('search-input'),
    searchSubmitBtn: document.getElementById('search-submit-btn'),
    cardsGrid: document.getElementById('cards-grid'),
    emptyState: document.getElementById('empty-results-state'),
    spinnerLoader: document.getElementById('spinner-loader'),
    resultsHeader: document.getElementById('results-header-container'),
    resultsCount: document.getElementById('results-count-badge'),
    resultsTitleText: document.getElementById('results-title-text'),
    netBadgeText: document.getElementById('network-name'),
    
    // Details Modal
    detailsModal: document.getElementById('details-modal'),
    closeDetailsBtn: document.getElementById('close-details-btn'),
    modalPoster: document.getElementById('modal-poster'),
    modalRating: document.getElementById('modal-rating'),
    modalQuality: document.getElementById('modal-quality'),
    modalType: document.getElementById('modal-type'),
    modalTitleText: document.getElementById('modal-title-text'),
    modalStoryText: document.getElementById('modal-story-text'),
    modalQuickPlayBtn: document.getElementById('modal-quick-play-btn'),
    
    // Seasons Section
    modalSeasonsSection: document.getElementById('modal-seasons-section'),
    modalSeasonsGrid: document.getElementById('modal-seasons-grid'),
    
    // Episodes Section
    modalEpisodesSection: document.getElementById('modal-episodes-section'),
    episodeFilterInput: document.getElementById('episode-filter-input'),
    modalEpisodesGrid: document.getElementById('modal-episodes-grid'),
    
    // Servers Section
    modalServersSection: document.getElementById('modal-servers-section'),
    modalServersList: document.getElementById('modal-servers-list'),
    serversLoader: document.getElementById('servers-loading-spinner'),
    
    // Player Modal
    playerModal: document.getElementById('player-modal'),
    closePlayerBtn: document.getElementById('close-player-btn'),
    playerTitleDisplay: document.getElementById('player-title-display'),
    playerRenderArea: document.getElementById('player-render-area'),
    playerServerBadge: document.getElementById('player-server-badge'),
    
    // Navigation Buttons
    navHomeBtn: document.getElementById('nav-home-btn'),
    navMoviesBtn: document.getElementById('nav-movies-btn'),
    navSeriesBtn: document.getElementById('nav-series-btn'),
    navAnimeBtn: document.getElementById('nav-anime-btn'),
    logoTrigger: document.getElementById('logo-trigger'),
    
    // Live Search Elements
    liveSearchDropdown: document.getElementById('live-search-dropdown'),
    liveSearchLoader: document.getElementById('live-search-loader'),
    liveSearchResults: document.getElementById('live-search-results')
};

// ============================================================================
// Core Event Bindings
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    elements.searchForm.addEventListener('submit', handleSearchSubmit);
    elements.closeDetailsBtn.onclick = closeDetailsModal;
    elements.closePlayerBtn.onclick = closePlayerModal;
    elements.episodeFilterInput.addEventListener('input', handleEpisodeFilter);
    
    // Live Search - debounced input handler
    let liveSearchTimer = null;
    elements.searchInput.addEventListener('input', () => {
        const query = elements.searchInput.value.trim();
        if (liveSearchTimer) clearTimeout(liveSearchTimer);
        if (!query || query.length < 2) {
            elements.liveSearchDropdown.style.display = 'none';
            return;
        }
        liveSearchTimer = setTimeout(() => performLiveSearch(query), 350);
    });
    
    // Close dropdown on clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrapper')) {
            elements.liveSearchDropdown.style.display = 'none';
        }
    });
    
    // Navigation Action Handlers
    elements.navHomeBtn.onclick = (e) => { e.preventDefault(); updateNavActive(elements.navHomeBtn); resetHomeUI(); };
    elements.logoTrigger.onclick = () => { updateNavActive(elements.navHomeBtn); resetHomeUI(); };
    elements.navMoviesBtn.onclick = (e) => { e.preventDefault(); updateNavActive(elements.navMoviesBtn); performSearch('__movies__', 'أحدث الأفلام المضافة'); };
    elements.navSeriesBtn.onclick = (e) => { e.preventDefault(); updateNavActive(elements.navSeriesBtn); performSearch('__series__', 'أحدث المسلسلات المضافة'); };
    elements.navAnimeBtn.onclick = (e) => { e.preventDefault(); updateNavActive(elements.navAnimeBtn); performSearch('__anime__', 'عالم الأنمي والكرتون'); };
    
    // Close modals on clicking overlay background
    elements.detailsModal.onclick = (e) => { if (e.target === elements.detailsModal) closeDetailsModal(); };
    elements.playerModal.onclick = (e) => { if (e.target === elements.playerModal) closePlayerModal(); };
    
    // Detect ISP connection
    detectNetwork();
    
    // Auto-load trending categories on startup
    resetHomeUI();
});

// Horizontal Carousel slider scroll control
window.scrollSlider = function(trackId, distance) {
    const track = document.getElementById(trackId);
    if (track) {
        // Adjust for RTL layout (scrolling left is negative, right is positive)
        track.scrollBy({ left: -distance, behavior: 'smooth' });
    }
};

// Open details for a card loaded inside a homepage carousel row
window.openDetailsModalByData = function(catIdx, cardIdx) {
    if (state.categories[catIdx] && state.categories[catIdx].cards[cardIdx]) {
        const item = state.categories[catIdx].cards[cardIdx];
        openDetailsModal(item);
    }
};

// ============================================================================
// Logic Handlers
// ============================================================================

function detectNetwork() {
    /** Dynamic Network Detection Badge */
    if (navigator.connection) {
        const type = navigator.connection.effectiveType || 'wifi';
        const rtt = navigator.connection.rtt || 'N/A';
        elements.netBadgeText.innerText = `السرعة: ${type.toUpperCase()} (الاستجابة: ${rtt}ms)`;
    } else {
        elements.netBadgeText.innerText = `الشبكة: متصل مباشر`;
    }
}

function updateNavActive(activeBtn) {
    [elements.navHomeBtn, elements.navMoviesBtn, elements.navSeriesBtn, elements.navAnimeBtn].forEach(btn => {
        if (btn) btn.classList.remove('active');
    });
    if (activeBtn) activeBtn.classList.add('active');
}

function handleSearchSubmit(e) {
    e.preventDefault();
    const query = elements.searchInput.value.trim();
    if (!query) return;
    updateNavActive(null); // Clear active navigation states
    elements.liveSearchDropdown.style.display = 'none'; // Hide dropdown on full submit
    performSearch(query);
}

async function performLiveSearch(query) {
    // Show dropdown with loader
    elements.liveSearchDropdown.style.display = 'block';
    elements.liveSearchLoader.style.display = 'block';
    elements.liveSearchResults.innerHTML = '';
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        elements.liveSearchLoader.style.display = 'none';
        
        const results = data.results || [];
        
        if (results.length === 0) {
            elements.liveSearchResults.innerHTML = `
                <div class="live-search-no-results">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    لا توجد نتائج لـ "${query}"
                </div>
            `;
            return;
        }
        
        // Show max 6 results in dropdown
        const displayResults = results.slice(0, 6);
        let html = '';
        
        displayResults.forEach((item) => {
            const posterSrc = item.poster || SVG_POSTER_PLACEHOLDER;
            html += `
                <div class="live-search-item" data-url="${item.url}" data-title="${item.title.replace(/"/g, '&quot;')}" data-poster="${posterSrc}" data-type="${item.type || 'فيلم'}" data-rating="${item.rating || '7.8'}" data-quality="${item.quality || '1080p'}">
                    <img class="live-search-item-poster" src="${posterSrc}" alt="${item.title}" onerror="this.src='${SVG_POSTER_PLACEHOLDER}'">
                    <div class="live-search-item-info">
                        <div class="live-search-item-title">${item.title}</div>
                        <div class="live-search-item-meta">
                            <span class="live-search-item-type">${item.type || 'فيلم'}</span>
                            <span class="live-search-item-quality">${item.quality || '1080p'}</span>
                        </div>
                    </div>
                    <i class="fa-solid fa-chevron-left live-search-item-arrow"></i>
                </div>
            `;
        });
        
        if (results.length > 6) {
            html += `
                <div class="live-search-view-all" id="live-search-view-all">
                    <i class="fa-solid fa-grid-2"></i>
                    عرض كل ${results.length} نتيجة
                </div>
            `;
        }
        
        elements.liveSearchResults.innerHTML = html;
        
        // Bind click events to each search result item
        elements.liveSearchResults.querySelectorAll('.live-search-item').forEach(el => {
            el.addEventListener('click', () => {
                const itemData = {
                    url: el.getAttribute('data-url'),
                    title: el.getAttribute('data-title'),
                    poster: el.getAttribute('data-poster'),
                    type: el.getAttribute('data-type'),
                    rating: el.getAttribute('data-rating'),
                    quality: el.getAttribute('data-quality')
                };
                elements.liveSearchDropdown.style.display = 'none';
                openDetailsModal(itemData);
            });
        });
        
        // Bind "view all" button
        const viewAllBtn = document.getElementById('live-search-view-all');
        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', () => {
                elements.liveSearchDropdown.style.display = 'none';
                elements.searchInput.value = query;
                updateNavActive(null);
                performSearch(query);
            });
        }
        
    } catch (e) {
        elements.liveSearchLoader.style.display = 'none';
        elements.liveSearchResults.innerHTML = `
            <div class="live-search-no-results">
                <i class="fa-solid fa-triangle-exclamation"></i>
                حدث خطأ أثناء البحث
            </div>
        `;
    }
}

async function performSearch(query, customTitle = null) {
    // UI Loading State
    elements.cardsGrid.innerHTML = '';
    elements.emptyState.style.display = 'none';
    elements.spinnerLoader.style.display = 'block';
    elements.resultsHeader.style.display = 'none';
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        elements.spinnerLoader.style.display = 'none';
        
        if (query === '__home__' && data.categories && data.categories.length > 0) {
            state.categories = data.categories;
            
            elements.resultsTitleText.innerHTML = `<i class="fa-solid fa-star animate-pulse" style="color: var(--accent-violet);"></i> مكتبة AleX CINEMA المضافة حديثاً`;
            elements.resultsCount.innerText = `${data.categories.length} تصنيف`;
            elements.resultsHeader.style.display = 'flex';
            
            renderCarousels(data.categories);
        } else if (data.results && data.results.length > 0) {
            state.searchResults = data.results;
            
            elements.resultsTitleText.innerHTML = `<i class="fa-solid fa-fire" style="color: var(--accent-blue);"></i> ${customTitle || `نتائج البحث عن: "${query}"`}`;
            elements.resultsCount.innerText = `${data.results.length} عرض`;
            elements.resultsHeader.style.display = 'flex';
            
            renderCards(data.results);
        } else {
            renderEmptyState(`عذراً، لم نجد أي عروض تطابق "${query}". جرب كلمات بحث أخرى.`);
        }
    } catch (e) {
        elements.spinnerLoader.style.display = 'none';
        renderEmptyState(`حدث خطأ أثناء تحميل البيانات: ${e.message}. يرجى التحقق من اتصال الشبكة.`);
    }
}

function getTypeIconClass(type) {
    const t = (type || '').toLowerCase().trim();
    if (t === 'فيلم' || t === 'movie') {
        return 'fa-solid fa-film';
    } else if (t === 'مسلسل' || t === 'tv' || t === 'series') {
        return 'fa-solid fa-tv';
    } else if (t === 'أنمي' || t === 'انمي' || t === 'anime') {
        return 'fa-solid fa-dragon';
    } else {
        return 'fa-solid fa-clapperboard';
    }
}

function renderCarousels(categories) {
    elements.cardsGrid.innerHTML = '';
    elements.cardsGrid.style.display = 'block'; // Convert grid to block layout for categorized rows
    
    categories.forEach((cat, idx) => {
        const row = document.createElement('div');
        row.className = 'category-row';
        
        const categoryId = `slider-track-${idx}`;
        let cardsHTML = '';
        
        cat.cards.forEach((item, cardIdx) => {
            const posterUrl = item.poster || SVG_POSTER_PLACEHOLDER;
            const rating = item.rating || '7.8';
            
            cardsHTML += `
                <div class="movie-card" onclick="window.openDetailsModalByData(${idx}, ${cardIdx})">
                    <div class="card-poster">
                        <img src="${posterUrl}" alt="${item.title}" class="card-poster-img" onerror="this.src='${SVG_POSTER_PLACEHOLDER}'">
                        <div class="poster-overlay">
                            <div class="play-hover-btn"><i class="fa-solid fa-play"></i></div>
                        </div>
                        <span class="card-rating-badge"><i class="fa-solid fa-star"></i> ${rating}</span>
                        <span class="card-quality-badge">${item.quality || '1080p'}</span>
                    </div>
                    <div class="card-body">
                        <h3 class="card-title">${item.title}</h3>
                        <div class="card-footer">
                            <span class="card-type"><i class="${getTypeIconClass(item.type)}"></i> ${item.type || 'فيلم'}</span>
                            <span class="card-action-hint">بث آمن</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        row.innerHTML = `
            <div class="category-header">
                <h3><i class="fa-solid fa-compact-disc animate-spin-slow" style="color: var(--accent-violet);"></i> ${cat.category}</h3>
            </div>
            <div class="category-slider-container">
                <button class="slider-arrow arrow-left" onclick="window.scrollSlider('${categoryId}', -350)"><i class="fa-solid fa-chevron-left"></i></button>
                <div class="category-slider-track" id="${categoryId}">
                    ${cardsHTML}
                </div>
                <button class="slider-arrow arrow-right" onclick="window.scrollSlider('${categoryId}', 350)"><i class="fa-solid fa-chevron-right"></i></button>
            </div>
        `;
        
        elements.cardsGrid.appendChild(row);
    });
}

function renderCards(results) {
    elements.cardsGrid.innerHTML = '';
    elements.cardsGrid.style.display = 'grid'; // Reset to standard flexbox/grid layout
    
    results.forEach((item, idx) => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.setAttribute('data-id', idx);
        
        card.onclick = () => openDetailsModal(item);
        
        const posterUrl = item.poster || SVG_POSTER_PLACEHOLDER;
        const rating = item.rating || '7.8';
        
        card.innerHTML = `
            <div class="card-poster">
                <img src="${posterUrl}" alt="${item.title}" class="card-poster-img" onerror="this.src='${SVG_POSTER_PLACEHOLDER}'">
                <div class="poster-overlay">
                    <div class="play-hover-btn"><i class="fa-solid fa-play"></i></div>
                </div>
                <span class="card-rating-badge"><i class="fa-solid fa-star"></i> ${rating}</span>
                <span class="card-quality-badge">${item.quality || '1080p'}</span>
            </div>
            <div class="card-body">
                <h3 class="card-title">${item.title}</h3>
                <div class="card-footer">
                    <span class="card-type"><i class="${getTypeIconClass(item.type)}"></i> ${item.type || 'عرض'}</span>
                    <span class="card-action-hint">بث آمن</span>
                </div>
            </div>
        `;
        
        elements.cardsGrid.appendChild(card);
    });
}

function renderEmptyState(message) {
    elements.cardsGrid.innerHTML = '';
    elements.resultsHeader.style.display = 'none';
    elements.emptyState.querySelector('h3').innerText = "لا توجد نتائج";
    elements.emptyState.querySelector('p').innerText = message;
    elements.emptyState.style.display = 'block';
}

function resetHomeUI() {
    elements.searchInput.value = '';
    performSearch('__home__', 'الرئيسية');
}

// ============================================================================
// Details Modal Overlay Handlers
// ============================================================================

async function openDetailsModal(item) {
    state.selectedItem = item;
    
    // Set static UI values
    elements.modalTitleText.innerText = item.title;
    elements.modalPoster.src = item.poster || SVG_POSTER_PLACEHOLDER;
    elements.modalRating.innerHTML = `<i class="fa-solid fa-star"></i> ${item.rating || '7.8'}`;
    elements.modalQuality.innerText = item.quality || '1080p FHD';
    elements.modalType.innerText = item.type || 'عرض سينمائي';
    
    // Loading State
    elements.modalStoryText.innerText = "جاري تحميل تفاصيل القصة وجدول الحلقات من مكتبة AleX CINEMA...";
    elements.modalSeasonsSection.style.display = 'none';
    elements.modalSeasonsGrid.innerHTML = '';
    elements.modalEpisodesSection.style.display = 'none';
    elements.modalQuickPlayBtn.style.display = 'none';
    state.bestServer = null;
    elements.modalServersList.innerHTML = '';
    elements.serversLoader.style.display = 'block';
    
    // Display Modal Panel
    elements.detailsModal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Lock background scroll
    
    loadSeasonData(item.url, "");
}

async function loadSeasonData(url, seasonTitle) {
    elements.modalEpisodesSection.style.display = 'none';
    elements.modalSeasonsSection.style.display = 'none';
    elements.modalQuickPlayBtn.style.display = 'none';
    elements.modalSeasonsGrid.innerHTML = '';
    elements.modalEpisodesGrid.innerHTML = '';
    elements.modalServersList.innerHTML = '';
    elements.serversLoader.style.display = 'block';
    
    try {
        const response = await fetch(`/api/details?url=${encodeURIComponent(url)}`);
        const details = await response.json();
        
        elements.modalStoryText.innerText = details.description || "لا توجد قصة متوفرة لهذا العرض حالياً.";
        
        if (details.is_series && details.seasons && details.seasons.length > 0) {
            elements.modalType.innerText = "مسلسل";
            state.seasons = details.seasons;
            
            // Render the seasons buttons
            renderSeasons(details.seasons);
            elements.modalSeasonsSection.style.display = 'block';
            
            // Identify active season or default to first
            let activeSeason = details.seasons.find(s => s.active || s.episodes.some(ep => ep.active));
            if (!activeSeason) {
                activeSeason = details.seasons[0];
            }
            
            // Highlight the active season button
            highlightActiveSeason(activeSeason.title);
            
            // Render this season's episodes
            state.currentEpisodes = activeSeason.episodes;
            renderEpisodes(activeSeason.episodes, activeSeason.title);
            elements.modalEpisodesSection.style.display = 'block';
            
            // Identify active episode or default to first
            const activeEp = activeSeason.episodes.find(ep => ep.active) || activeSeason.episodes[0];
            if (activeEp) {
                highlightActiveEpisode(activeEp.url);
                
                const displayTitle = `${state.selectedItem.title} - ${activeSeason.title} - ${activeEp.title}`;
                fetchStreamingServers(
                    activeEp.url, 
                    displayTitle, 
                    state.selectedItem.title, 
                    true, 
                    activeSeason.title, 
                    activeEp.title
                );
            } else {
                elements.serversLoader.style.display = 'none';
            }
        } else {
            elements.modalType.innerText = "فيلم";
            // For movies
            fetchStreamingServers(url, state.selectedItem.title, state.selectedItem.title, false, "", "");
        }
    } catch (e) {
        elements.modalStoryText.innerText = `فشل تحميل تفاصيل العرض: ${e.message}`;
        elements.serversLoader.style.display = 'none';
    }
}

function renderSeasons(seasons) {
    elements.modalSeasonsGrid.innerHTML = '';
    
    seasons.forEach((season) => {
        const btn = document.createElement('button');
        btn.className = 'season-btn';
        btn.innerText = season.title;
        btn.title = season.title;
        btn.setAttribute('data-title', season.title);
        
        btn.onclick = () => {
            elements.modalSeasonsGrid.querySelectorAll('.season-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            state.currentEpisodes = season.episodes;
            renderEpisodes(season.episodes, season.title);
            
            const firstEp = season.episodes[0];
            if (firstEp) {
                highlightActiveEpisode(firstEp.url);
                const displayTitle = `${state.selectedItem.title} - ${season.title} - ${firstEp.title}`;
                fetchStreamingServers(
                    firstEp.url, 
                    displayTitle, 
                    state.selectedItem.title, 
                    true, 
                    season.title, 
                    firstEp.title
                );
            }
        };
        
        elements.modalSeasonsGrid.appendChild(btn);
    });
}

function highlightActiveSeason(seasonTitle) {
    const buttons = elements.modalSeasonsGrid.querySelectorAll('.season-btn');
    buttons.forEach(btn => {
        if (btn.getAttribute('data-title') === seasonTitle) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function renderEpisodes(episodes, seasonTitle = "") {
    elements.modalEpisodesGrid.innerHTML = '';
    
    episodes.forEach((ep) => {
        const btn = document.createElement('button');
        btn.className = `episode-btn ${ep.active ? 'active' : ''}`;
        btn.innerText = ep.title;
        btn.title = ep.title;
        btn.setAttribute('data-url', ep.url);
        
        btn.onclick = () => {
            elements.modalEpisodesGrid.querySelectorAll('.episode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const displayTitle = seasonTitle ? `${state.selectedItem.title} - ${seasonTitle} - ${ep.title}` : `${state.selectedItem.title} - ${ep.title}`;
            fetchStreamingServers(
                ep.url, 
                displayTitle, 
                state.selectedItem.title, 
                true, 
                seasonTitle, 
                ep.title
            );
        };
        
        elements.modalEpisodesGrid.appendChild(btn);
    });
}

function highlightActiveEpisode(activeUrl) {
    const buttons = elements.modalEpisodesGrid.querySelectorAll('.episode-btn');
    buttons.forEach(btn => {
        if (btn.getAttribute('data-url') === activeUrl) {
            btn.classList.add('active');
            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            btn.classList.remove('active');
        }
    });
}

function handleEpisodeFilter() {
    const filter = elements.episodeFilterInput.value.toLowerCase().trim();
    const filtered = state.currentEpisodes.filter(ep => ep.title.toLowerCase().includes(filter));
    
    elements.modalEpisodesGrid.innerHTML = '';
    
    // Find active season title
    const activeSeasonBtn = elements.modalSeasonsGrid.querySelector('.season-btn.active');
    const seasonTitle = activeSeasonBtn ? activeSeasonBtn.getAttribute('data-title') : "";
    
    filtered.forEach((ep) => {
        const btn = document.createElement('button');
        btn.className = `episode-btn ${ep.active ? 'active' : ''}`;
        btn.innerText = ep.title;
        btn.setAttribute('data-url', ep.url);
        
        btn.onclick = () => {
            elements.modalEpisodesGrid.querySelectorAll('.episode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const displayTitle = seasonTitle ? `${state.selectedItem.title} - ${seasonTitle} - ${ep.title}` : `${state.selectedItem.title} - ${ep.title}`;
            fetchStreamingServers(
                ep.url, 
                displayTitle, 
                state.selectedItem.title, 
                true, 
                seasonTitle, 
                ep.title
            );
        };
        
        elements.modalEpisodesGrid.appendChild(btn);
    });
}

async function fetchStreamingServers(url, displayTitle, title = "", isSeries = false, season = "", episode = "") {
    elements.modalServersList.innerHTML = '';
    elements.serversLoader.style.display = 'block';
    elements.modalQuickPlayBtn.style.display = 'none';
    
    try {
        let apiUrl = `/api/watch?url=${encodeURIComponent(url)}`;
        if (title) {
            apiUrl += `&title=${encodeURIComponent(title)}&is_series=${isSeries}&season=${encodeURIComponent(season)}&episode=${encodeURIComponent(episode)}`;
        }
        
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        elements.serversLoader.style.display = 'none';
        
        if (data.servers && data.servers.length > 0) {
            state.activeServerList = data.servers;
            renderServers(data.servers, displayTitle);
            
            // Automatically select the BEST server (prefer direct, then fallback to first available)
            const bestServer = data.servers.find(s => s.type === 'direct') || data.servers[0];
            state.bestServer = bestServer;
            
            // Configure the prominent Quick Play button
            if (state.bestServer && state.bestServer.url !== 'about:blank') {
                elements.modalQuickPlayBtn.style.display = 'flex';
                elements.modalQuickPlayBtn.innerHTML = `<i class="fa-solid fa-play"></i> مشاهدة الآن (بأعلى جودة)`;
                elements.modalQuickPlayBtn.onclick = () => {
                    launchPlayer(state.bestServer, displayTitle);
                };
            } else {
                elements.modalQuickPlayBtn.style.display = 'flex';
                elements.modalQuickPlayBtn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> العرض غير متوفر حالياً`;
                elements.modalQuickPlayBtn.onclick = null;
            }
        } else {
            elements.modalQuickPlayBtn.style.display = 'flex';
            elements.modalQuickPlayBtn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> العرض غير متوفر حالياً`;
            elements.modalQuickPlayBtn.onclick = null;
        }
    } catch (e) {
        elements.serversLoader.style.display = 'none';
        elements.modalQuickPlayBtn.style.display = 'flex';
        elements.modalQuickPlayBtn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> فشل توليد روابط البث`;
        elements.modalQuickPlayBtn.onclick = null;
    }
}

function renderServers(servers, displayTitle) {
    elements.modalServersList.innerHTML = '';
    
    servers.forEach((server) => {
        const btn = document.createElement('button');
        
        if (server.type === 'direct') {
            btn.className = 'server-item-btn direct-server';
            btn.innerHTML = `
                <span><i class="fa-solid fa-shield-heart"></i> ${server.server}</span>
                <span class="server-action-hint"><i class="fa-solid fa-play server-action-icon"></i> تشغيل فوري نظيف</span>
            `;
        } else {
            btn.className = 'server-item-btn';
            btn.innerHTML = `
                <span><i class="fa-solid fa-server"></i> ${server.server}</span>
                <span class="server-action-hint"><i class="fa-solid fa-play server-action-icon"></i> مشغل ويب معزول</span>
            `;
        }
        
        btn.onclick = () => {
            if (server.url !== 'about:blank') {
                launchPlayer(server, displayTitle);
            }
        };
        elements.modalServersList.appendChild(btn);
    });
}

function closeDetailsModal() {
    elements.detailsModal.style.display = 'none';
    document.body.style.overflow = 'auto'; // Unlock scroll
}

// ============================================================================
// Immersive Cinema Player Modal Handlers
// ============================================================================

// LocalStorage key helper
function getProgressKey(url) {
    return `alex_cinema_progress_${url}`;
}

function loadPlayerSource(server, startTime = 0, autoplay = true) {
    state.currentPlayingServer = server;
    elements.playerServerBadge.innerText = server.server;
    
    // Display Custom Elegant Loading Overlay inside player
    const customLoader = document.getElementById('player-custom-loader');
    const loaderStatus = document.getElementById('player-loader-status');
    if (customLoader && loaderStatus) {
        customLoader.style.display = 'flex';
        loaderStatus.innerText = "جارِ تأمين اتصال البث المباشر الآمن...";
        
        // Dynamic transitioning status messages
        state.loaderIntervals = [];
        state.loaderIntervals.push(setTimeout(() => { loaderStatus.innerText = "جارِ فك تشفير مسارات البث السينمائي الفائق..."; }, 400));
        state.loaderIntervals.push(setTimeout(() => { loaderStatus.innerText = "جارِ تهيئة البث بأعلى جودة متوفرة..."; }, 800));
    }
    
    // Clean existing Hls instance if present
    if (state.hlsInstance) {
        state.hlsInstance.destroy();
        state.hlsInstance = null;
    }
    
    const video = document.getElementById('video-player');
    if (!video) return;
    
    // Check if progress exists in localStorage to resume playing
    let progressTime = startTime;
    if (progressTime === 0) {
        const savedTime = localStorage.getItem(getProgressKey(server.url));
        if (savedTime) {
            progressTime = parseFloat(savedTime);
            console.log("Resuming progress from Saved Time:", progressTime);
        }
    }
    
    const hideLoaderSmoothly = () => {
        if (customLoader) {
            customLoader.style.transition = 'opacity 0.4s ease';
            customLoader.style.opacity = '0';
            setTimeout(() => {
                customLoader.style.display = 'none';
                customLoader.style.opacity = '1';
            }, 400);
        }
        // Clear status transition timers
        if (state.loaderIntervals) {
            state.loaderIntervals.forEach(t => clearTimeout(t));
        }
    };
    
    if (server.url.includes('.m3u8')) {
        // HLS Stream (.m3u8) using Hls.js
        if (Hls.isSupported()) {
            const hls = new Hls({
                maxBufferLength: 30,
                maxMaxBufferLength: 60,
                enableWorker: true,
                lowLatencyMode: true,
                xhrSetup: function(xhr, url) {
                    xhr.withCredentials = false;
                }
            });
            hls.loadSource(server.url);
            hls.attachMedia(video);
            state.hlsInstance = hls;
            
            hls.on(Hls.Events.MANIFEST_PARSED, function() {
                if (progressTime > 0) {
                    video.currentTime = progressTime;
                }
                if (autoplay) {
                    state.activePlayer.play().catch(()=>{});
                }
                hideLoaderSmoothly();
            });
            
            // Seamless Hls.js error recovery
            hls.on(Hls.Events.ERROR, function(event, data) {
                if (data.fatal) {
                    switch (data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.warn("HLS Network Error, attempting reload...");
                            hls.startLoad();
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.warn("HLS Media Error, attempting recovery...");
                            hls.recoverMediaError();
                            break;
                        default:
                            console.error("HLS Unrecoverable Error, destroying pipeline.");
                            hls.destroy();
                            break;
                    }
                }
            });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // iOS / Safari Native HLS support
            video.src = server.url;
            const onLoaded = () => {
                if (progressTime > 0) video.currentTime = progressTime;
                if (autoplay) state.activePlayer.play().catch(()=>{});
                hideLoaderSmoothly();
                video.removeEventListener('loadedmetadata', onLoaded);
            };
            video.addEventListener('loadedmetadata', onLoaded);
        }
    } else {
        // Direct MP4 Stream
        video.src = server.url;
        const onLoaded = () => {
            if (progressTime > 0) video.currentTime = progressTime;
            if (autoplay) state.activePlayer.play().catch(()=>{});
            hideLoaderSmoothly();
            video.removeEventListener('loadedmetadata', onLoaded);
        };
        video.addEventListener('loadedmetadata', onLoaded);
    }
}

function showCenterIndicator(iconClass, persistent = false) {
    const indicator = document.getElementById('player-center-indicator');
    if (!indicator) return;
    
    // Set the icon
    indicator.innerHTML = `<i class="${iconClass}"></i>`;
    
    // Clear any pending hide timer
    if (state.indicatorTimeout) {
        clearTimeout(state.indicatorTimeout);
        state.indicatorTimeout = null;
    }
    
    // Reset animation classes
    indicator.classList.remove('trigger-anim');
    indicator.style.display = 'flex';
    
    if (persistent) {
        // Persistent mode: stays visible (used for paused state play icon)
        indicator.classList.remove('trigger-anim');
        indicator.style.opacity = '1';
        return;
    }
    
    // Brief flash mode: animate and auto-hide
    void indicator.offsetWidth;
    indicator.classList.add('trigger-anim');
    
    state.indicatorTimeout = setTimeout(() => {
        indicator.style.display = 'none';
        indicator.classList.remove('trigger-anim');
    }, 500);
}



function handleKeyboardShortcuts(e) {
    if (!state.activePlayer) return;
    
    // Prevent shortcut firing if user is writing in input or search fields
    if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) {
        return;
    }
    
    const code = e.code;
    const handledCodes = [
        'Space', 'KeyK',
        'ArrowLeft', 'KeyJ',
        'ArrowRight', 'KeyL',
        'ArrowUp', 'ArrowDown',
        'KeyF', 'KeyM',
        'Period', 'Comma',
        'Digit0', 'Digit1', 'Digit2', 'Digit3', 'Digit4',
        'Digit5', 'Digit6', 'Digit7', 'Digit8', 'Digit9'
    ];
    
    if (handledCodes.includes(code)) {
        e.preventDefault();
        e.stopPropagation();
    } else {
        return;
    }
    
    switch (code) {
        case 'Space':
        case 'KeyK': // Toggle Play/Pause
            if (state.activePlayer.paused) {
                state.activePlayer.play().catch(()=>{});
            } else {
                state.activePlayer.pause();
            }
            break;
            
        case 'ArrowRight':
        case 'KeyL': // Seek Forward 10s
            state.activePlayer.currentTime = Math.min(state.activePlayer.duration || 0, state.activePlayer.currentTime + 10);
            showCenterIndicator('fa-solid fa-forward');
            break;
            
        case 'ArrowLeft':
        case 'KeyJ': // Seek Backward 10s
            state.activePlayer.currentTime = Math.max(0, state.activePlayer.currentTime - 10);
            showCenterIndicator('fa-solid fa-backward');
            break;
            
        case 'ArrowUp': // Volume Up 10%
            state.activePlayer.volume = Math.min(1, state.activePlayer.volume + 0.1);
            showCenterIndicator('fa-solid fa-volume-high');
            break;
            
        case 'ArrowDown': // Volume Down 10%
            state.activePlayer.volume = Math.max(0, state.activePlayer.volume - 0.1);
            showCenterIndicator(state.activePlayer.volume === 0 ? 'fa-solid fa-volume-xmark' : 'fa-solid fa-volume-low');
            break;
            
        case 'KeyF': // Fullscreen Toggle
            state.activePlayer.fullscreen.toggle();
            break;
            
        case 'KeyM': // Mute Toggle
            state.activePlayer.muted = !state.activePlayer.muted;
            showCenterIndicator(state.activePlayer.muted ? 'fa-solid fa-volume-xmark' : 'fa-solid fa-volume-high');
            break;
            
        case 'Period': // Increase playback speed (Shift + >)
            if (e.shiftKey) {
                const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
                let currentSpeed = state.activePlayer.speed;
                let nextIdx = speeds.indexOf(currentSpeed) + 1;
                if (nextIdx < speeds.length) {
                    state.activePlayer.speed = speeds[nextIdx];
                    showCenterIndicator('fa-solid fa-gauge-high');
                }
            }
            break;
            
        case 'Comma': // Decrease playback speed (Shift + <)
            if (e.shiftKey) {
                const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
                let currentSpeed = state.activePlayer.speed;
                let prevIdx = speeds.indexOf(currentSpeed) - 1;
                if (prevIdx >= 0) {
                    state.activePlayer.speed = speeds[prevIdx];
                    showCenterIndicator('fa-solid fa-gauge-simple');
                }
            }
            break;
            
        default:
            // Handle numeric keys Digit0-Digit9 to seek directly to that percentage of the video
            if (code.startsWith('Digit')) {
                const digit = parseInt(code.replace('Digit', ''));
                if (state.activePlayer.duration) {
                    state.activePlayer.currentTime = state.activePlayer.duration * (digit / 10);
                    showCenterIndicator('fa-solid fa-arrow-right-to-bracket');
                }
            }
            break;
    }
}

function setupAutoplayNext(currentUrl) {
    const nextEpisodeCard = document.getElementById('player-next-episode-card');
    const nextEpisodeTitle = document.getElementById('player-next-episode-title');
    const nextEpisodeSkipBtn = document.getElementById('player-next-skip-btn');
    const progressRing = document.getElementById('countdown-progress-ring');
    const countdownText = document.getElementById('player-next-countdown-text');
    
    if (!nextEpisodeCard || !nextEpisodeTitle || !nextEpisodeSkipBtn || !progressRing || !countdownText) return;
    
    // Hide card initially
    nextEpisodeCard.style.display = 'none';
    
    if (state.selectedItem && state.selectedItem.type === 'مسلسل' && state.currentEpisodes && state.currentEpisodes.length > 0) {
        // Find index of current episode
        const currentIdx = state.currentEpisodes.findIndex(ep => ep.url === currentUrl);
        if (currentIdx !== -1 && currentIdx + 1 < state.currentEpisodes.length) {
            const nextEp = state.currentEpisodes[currentIdx + 1];
            
            // Set title
            nextEpisodeTitle.innerText = nextEp.title;
            
            // Listen to ended event on player
            const onEpisodeEnded = () => {
                // Show countdown card overlay inside player
                nextEpisodeCard.style.display = 'flex';
                
                let secondsLeft = 5;
                countdownText.innerText = secondsLeft;
                
                // Animate progress ring
                progressRing.style.strokeDasharray = "100, 100";
                
                const triggerNextEpisode = () => {
                    clearInterval(state.countdownTimer);
                    nextEpisodeCard.style.display = 'none';
                    
                    // Highlight the next episode button in details grid silently
                    highlightActiveEpisode(nextEp.url);
                    
                    // Build next display title
                    const activeSeasonBtn = elements.modalSeasonsGrid.querySelector('.season-btn.active');
                    const seasonTitle = activeSeasonBtn ? activeSeasonBtn.getAttribute('data-title') : "";
                    const nextDisplayTitle = seasonTitle ? `${state.selectedItem.title} - ${seasonTitle} - ${nextEp.title}` : `${state.selectedItem.title} - ${nextEp.title}`;
                    
                    // Trigger resolved list update silently, then play!
                    fetchStreamingServers(
                        nextEp.url, 
                        nextDisplayTitle, 
                        state.selectedItem.title, 
                        true, 
                        seasonTitle, 
                        nextEp.title
                    ).then(() => {
                        // Launch the new stream
                        if (state.bestServer) {
                            launchPlayer(state.bestServer, nextDisplayTitle);
                        }
                    });
                };
                
                nextEpisodeSkipBtn.onclick = () => {
                    triggerNextEpisode();
                };
                
                state.countdownTimer = setInterval(() => {
                    secondsLeft -= 1;
                    countdownText.innerText = Math.max(0, secondsLeft);
                    
                    // Calculate stroke ring dash offset
                    const percentage = (secondsLeft / 5) * 100;
                    progressRing.style.strokeDasharray = `${percentage}, 100`;
                    
                    if (secondsLeft <= 0) {
                        triggerNextEpisode();
                    }
                }, 1000);
            };
            
            state.activePlayer.on('ended', onEpisodeEnded);
        }
    }
}

function launchPlayer(server, title) {
    elements.playerTitleDisplay.innerText = title;
    elements.playerRenderArea.innerHTML = '';
    
    // Hide overlays initially
    const nextEpisodeCard = document.getElementById('player-next-episode-card');
    if (nextEpisodeCard) nextEpisodeCard.style.display = 'none';
    const centerIndicator = document.getElementById('player-center-indicator');
    if (centerIndicator) centerIndicator.style.display = 'none';
    
    // Display Player Overlay Panel
    elements.playerModal.style.display = 'flex';
    
    const video = document.createElement('video');
    video.id = 'video-player';
    video.className = 'plyr-video-player';
    video.setAttribute('playsinline', '');
    video.setAttribute('controls', '');
    video.setAttribute('preload', 'auto');
    if (state.selectedItem && state.selectedItem.poster) {
        video.setAttribute('poster', state.selectedItem.poster);
    }
    
    elements.playerRenderArea.appendChild(video);
    
    // Extract available quality resolutions
    const qualityOptions = [];
    state.activeServerList.forEach(srv => {
        const qMatch = srv.server.match(/(\d+)/);
        if (qMatch) {
            qualityOptions.push(parseInt(qMatch[1]));
        }
    });
    const uniqueQualityOptions = [...new Set(qualityOptions)].sort((a, b) => b - a);
    
    const initialQMatch = server.server.match(/(\d+)/);
    const defaultQuality = initialQMatch ? parseInt(initialQMatch[1]) : (uniqueQualityOptions[0] || 1080);
    
    // Initialize Plyr with native settings menu quality options
    state.activePlayer = new Plyr(video, {
        controls: [
            'play-large', 'play', 'progress', 'current-time', 'duration',
            'mute', 'volume', 'settings', 'pip', 'fullscreen'
        ],
        settings: ['quality', 'speed'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        quality: {
            default: defaultQuality,
            options: uniqueQualityOptions,
            forced: true,
            onChange: (newQuality) => {
                const currentQMatch = state.currentPlayingServer ? state.currentPlayingServer.server.match(/(\d+)/) : null;
                const currentQuality = currentQMatch ? parseInt(currentQMatch[1]) : null;
                
                if (currentQuality === newQuality) return;
                
                const targetServer = state.activeServerList.find(srv => {
                    const qMatch = srv.server.match(/(\d+)/);
                    const size = qMatch ? parseInt(qMatch[1]) : 1080;
                    return size === newQuality;
                });
                
                if (targetServer) {
                    const currentTime = state.activePlayer ? state.activePlayer.currentTime : 0;
                    const isPlaying = state.activePlayer ? !state.activePlayer.paused : true;
                    console.log("Player quality switched in gear settings menu to:", newQuality);
                    loadPlayerSource(targetServer, currentTime, isPlaying);
                }
            }
        },
        tooltips: { controls: true, seek: true }
    });
    
    // Setup Playback progress saver (save current time every 2 seconds)
    state.progressSaveTimer = setInterval(() => {
        if (state.activePlayer && !state.activePlayer.paused && state.activePlayer.currentTime > 5) {
            // Only save if progress is less than 95% complete to prevent looping completed videos
            if (state.activePlayer.currentTime < state.activePlayer.duration * 0.95) {
                localStorage.setItem(getProgressKey(server.url), state.activePlayer.currentTime);
            } else {
                localStorage.removeItem(getProgressKey(server.url)); // remove completed progress
            }
        }
    }, 2000);
    
    // Bind Advanced Keyboard control listener in CAPTURING phase
    window.addEventListener('keydown', handleKeyboardShortcuts, true);
    
    // Single Click & Double Click gesture actions inside a unified Click handler in CAPTURING phase
    state.clickTimer = null;
    state.playerClickListener = (e) => {
        // Only capture and coordinate clicks directly on the video viewport wrapper
        const isVideoClick = e.target.closest('.plyr__video-wrapper') || e.target.tagName === 'VIDEO';
        if (!isVideoClick) return; // Let all other clicks (like controls, menus, etc.) pass through normally!
        
        e.preventDefault();
        e.stopPropagation();
        
        if (state.clickTimer) {
            // Double Click Gesture Detected!
            clearTimeout(state.clickTimer);
            state.clickTimer = null;
            
            // Get bounding rect of the actual active Plyr container to support flawless coordinates in both standard and fullscreen views
            const plyrContainer = elements.playerRenderArea.querySelector('.plyr');
            const rect = plyrContainer ? plyrContainer.getBoundingClientRect() : elements.playerRenderArea.getBoundingClientRect();
            const tapX = e.clientX - rect.left;
            const widthPercent = (tapX / rect.width) * 100;
            
            if (widthPercent > 65) {
                // Double click on right: Fast Forward 10s
                state.activePlayer.currentTime = Math.min(state.activePlayer.duration || 0, state.activePlayer.currentTime + 10);
                showCenterIndicator('fa-solid fa-forward-step');
            } else if (widthPercent < 35) {
                // Double click on left: Seek back 10s
                state.activePlayer.currentTime = Math.max(0, state.activePlayer.currentTime - 10);
                showCenterIndicator('fa-solid fa-backward-step');
            } else {
                // Double click in middle: Toggle Fullscreen
                state.activePlayer.fullscreen.toggle();
            }
        } else {
            // Wait for 250ms to distinguish from double click
            state.clickTimer = setTimeout(() => {
                state.clickTimer = null;
                
                // Single Click Toggle Play/Pause
                if (state.activePlayer) {
                    if (state.activePlayer.paused) {
                        state.activePlayer.play().catch(()=>{});
                    } else {
                        state.activePlayer.pause();
                    }
                }
            }, 250);
        }
    };
    
    elements.playerRenderArea.addEventListener('click', state.playerClickListener, true);
    
    // Block native dblclick events on video viewport in capturing phase to prevent Plyr overlay takeovers
    state.playerDblClickListener = (e) => {
        const isVideoClick = e.target.closest('.plyr__video-wrapper') || e.target.tagName === 'VIDEO';
        if (!isVideoClick) return;
        
        e.preventDefault();
        e.stopPropagation();
    };
    elements.playerRenderArea.addEventListener('dblclick', state.playerDblClickListener, true);
    
    // Setup next episode autoplay
    setupAutoplayNext(server.url);
    
    // Load initial source
    loadPlayerSource(server, 0, true);
}

function closePlayerModal() {
    // Clear Saved save progress timer
    if (state.progressSaveTimer) {
        clearInterval(state.progressSaveTimer);
    }
    if (state.countdownTimer) {
        clearInterval(state.countdownTimer);
    }
    if (state.loaderIntervals) {
        state.loaderIntervals.forEach(t => clearTimeout(t));
    }
    
    // Unbind Keyboard shortcuts in CAPTURING phase
    window.removeEventListener('keydown', handleKeyboardShortcuts, true);
    
    if (state.clickTimer) {
        clearTimeout(state.clickTimer);
        state.clickTimer = null;
    }
    
    if (state.playerClickListener) {
        elements.playerRenderArea.removeEventListener('click', state.playerClickListener, true);
        state.playerClickListener = null;
    }
    
    if (state.playerDblClickListener) {
        elements.playerRenderArea.removeEventListener('dblclick', state.playerDblClickListener, true);
        state.playerDblClickListener = null;
    }
    
    if (state.activePlayer) {
        state.activePlayer.destroy();
        state.activePlayer = null;
    }
    
    if (state.hlsInstance) {
        state.hlsInstance.destroy();
        state.hlsInstance = null;
    }
    
    state.currentPlayingServer = null;
    elements.playerRenderArea.innerHTML = '';
    elements.playerModal.style.display = 'none';
}

