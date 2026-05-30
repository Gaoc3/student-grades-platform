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
    logoTrigger: document.getElementById('logo-trigger')
};

// ============================================================================
// Core Event Bindings
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    elements.searchForm.addEventListener('submit', handleSearchSubmit);
    elements.closeDetailsBtn.onclick = closeDetailsModal;
    elements.closePlayerBtn.onclick = closePlayerModal;
    elements.episodeFilterInput.addEventListener('input', handleEpisodeFilter);
    
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
    performSearch(query);
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
            
            elements.resultsTitleText.innerHTML = `<i class="fa-solid fa-star text-red-500 animate-pulse"></i> مكتبة سينمانا المضافة حديثاً`;
            elements.resultsCount.innerText = `${data.categories.length} تصنيف`;
            elements.resultsHeader.style.display = 'flex';
            
            renderCarousels(data.categories);
        } else if (data.results && data.results.length > 0) {
            state.searchResults = data.results;
            
            elements.resultsTitleText.innerHTML = `<i class="fa-solid fa-fire text-red-500"></i> ${customTitle || `نتائج البحث عن: "${query}"`}`;
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
                            <span class="card-type"><i class="fa-solid fa-circle-chevron-right"></i> ${item.type || 'فيلم'}</span>
                            <span class="card-action-hint">بث آمن</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        row.innerHTML = `
            <div class="category-header">
                <h3><i class="fa-solid fa-compact-disc text-red-500 animate-spin-slow"></i> ${cat.category}</h3>
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
                    <span class="card-type"><i class="fa-solid fa-circle-chevron-right"></i> ${item.type || 'عرض'}</span>
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
    elements.modalStoryText.innerText = "جاري تحميل تفاصيل القصة وجدول الحلقات من سينمانا شبكتي...";
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
    elements.modalQuickPlayBtn.style.display = 'none';
    elements.modalServersList.innerHTML = '';
    elements.serversLoader.style.display = 'block';
    
    try {
        const response = await fetch(`/api/details?url=${encodeURIComponent(url)}`);
        const details = await response.json();
        
        elements.modalStoryText.innerText = details.description || "لا توجد قصة متوفرة لهذا العرض حالياً.";
        
        if (details.is_series && details.episodes && details.episodes.length > 0) {
            state.currentEpisodes = details.episodes;
            renderEpisodes(details.episodes, seasonTitle);
            elements.modalEpisodesSection.style.display = 'block';
            
            // Trigger server fetching automatically for the CURRENT ACTIVE episode
            const activeEp = details.episodes.find(ep => ep.active) || details.episodes[0];
            const displayTitle = seasonTitle ? `${state.selectedItem.title} - ${seasonTitle} - ${activeEp.title}` : `${state.selectedItem.title} - ${activeEp.title}`;
            fetchStreamingServers(activeEp.url, displayTitle);
        } else {
            // For movies
            fetchStreamingServers(url, state.selectedItem.title);
        }
    } catch (e) {
        elements.modalStoryText.innerText = `فشل تحميل تفاصيل العرض: ${e.message}`;
        elements.serversLoader.style.display = 'none';
    }
}

function renderEpisodes(episodes, seasonTitle = "") {
    elements.modalEpisodesGrid.innerHTML = '';
    
    episodes.forEach((ep) => {
        const btn = document.createElement('button');
        btn.className = `episode-btn ${ep.active ? 'active' : ''}`;
        btn.innerText = ep.title;
        btn.title = ep.title;
        
        btn.onclick = () => {
            elements.modalEpisodesGrid.querySelectorAll('.episode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const displayTitle = seasonTitle ? `${state.selectedItem.title} - ${seasonTitle} - ${ep.title}` : `${state.selectedItem.title} - ${ep.title}`;
            fetchStreamingServers(ep.url, displayTitle);
        };
        
        elements.modalEpisodesGrid.appendChild(btn);
    });
}

function handleEpisodeFilter() {
    const filter = elements.episodeFilterInput.value.toLowerCase().trim();
    const filtered = state.currentEpisodes.filter(ep => ep.title.toLowerCase().includes(filter));
    
    elements.modalEpisodesGrid.innerHTML = '';
    filtered.forEach((ep) => {
        const btn = document.createElement('button');
        btn.className = `episode-btn ${ep.active ? 'active' : ''}`;
        btn.innerText = ep.title;
        
        btn.onclick = () => {
            elements.modalEpisodesGrid.querySelectorAll('.episode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const displayTitle = `${state.selectedItem.title} - ${ep.title}`;
            fetchStreamingServers(ep.url, displayTitle);
        };
        
        elements.modalEpisodesGrid.appendChild(btn);
    });
}

async function fetchStreamingServers(url, displayTitle) {
    elements.modalServersList.innerHTML = '';
    elements.serversLoader.style.display = 'block';
    elements.modalQuickPlayBtn.style.display = 'none';
    
    try {
        const response = await fetch(`/api/watch?url=${encodeURIComponent(url)}`);
        const data = await response.json();
        
        elements.serversLoader.style.display = 'none';
        
        if (data.servers && data.servers.length > 0) {
            state.activeServerList = data.servers;
            renderServers(data.servers, displayTitle);
            
            // Automatically select the BEST server (prefer direct, then fallback to first)
            const bestServer = data.servers.find(s => s.type === 'direct') || data.servers[0];
            state.bestServer = bestServer;
            
            // Configure the prominent Quick Play button
            if (state.bestServer && state.bestServer.url !== 'about:blank') {
                elements.modalQuickPlayBtn.style.display = 'flex';
                elements.modalQuickPlayBtn.onclick = () => {
                    if (state.bestServer) {
                        launchPlayer(state.bestServer, displayTitle);
                    }
                };
            }
        } else {
            elements.modalServersList.innerHTML = `<p class="error-text"><i class="fa-solid fa-triangle-exclamation"></i> عذراً، لا توجد سيرفرات بث آمنة متوفرة حالياً لهذا العرض.</p>`;
        }
    } catch (e) {
        elements.serversLoader.style.display = 'none';
        elements.modalServersList.innerHTML = `<p class="error-text">فشل جلب سيرفرات التشغيل: ${e.message}</p>`;
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

function launchPlayer(server, title) {
    elements.playerTitleDisplay.innerText = title;
    elements.playerServerBadge.innerText = server.server;
    elements.playerRenderArea.innerHTML = '';
    
    // Display Player Overlay Panel
    elements.playerModal.style.display = 'flex';
    
    if (server.type === 'direct') {
        // Direct MP4 stream -> HTML5 Video with Plyr.js (100% AD-FREE!)
        const video = document.createElement('video');
        video.id = 'video-player';
        video.className = 'video-js vjs-fluid';
        video.setAttribute('playsinline', '');
        video.setAttribute('controls', '');
        video.setAttribute('preload', 'auto');
        
        const source = document.createElement('source');
        source.src = server.url;
        source.type = 'video/mp4';
        
        video.appendChild(source);
        elements.playerRenderArea.appendChild(video);
        
        // Initialize Plyr with premium red styling
        state.activePlayer = new Plyr('#video-player', {
            controls: [
                'play-large', 'play', 'progress', 'current-time', 'duration',
                'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen'
            ],
            settings: ['quality', 'speed'],
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
            tooltips: { controls: true, seek: true }
        });
        
        state.activePlayer.play();
    } else {
        // Fallback -> Sandboxed Iframe (STRICT POPUP BLOCKING!)
        const iframe = document.createElement('iframe');
        iframe.src = server.url;
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-presentation');
        iframe.setAttribute('allowfullscreen', 'true');
        iframe.setAttribute('scrolling', 'no');
        
        elements.playerRenderArea.appendChild(iframe);
        state.activePlayer = null;
    }
}

function closePlayerModal() {
    if (state.activePlayer) {
        state.activePlayer.destroy();
        state.activePlayer = null;
    }
    
    elements.playerRenderArea.innerHTML = '';
    elements.playerModal.style.display = 'none';
}
