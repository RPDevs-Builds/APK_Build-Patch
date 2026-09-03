document.addEventListener("DOMContentLoaded", () => {
    const appsGrid = document.getElementById("appsGrid");
    const searchInput = document.getElementById("searchInput");
    const categoryButtons = document.querySelectorAll(".cat-pill");
    const qrModal = document.getElementById("qrModal");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const modalAppTitle = document.getElementById("modalAppTitle");
    const modalQrImg = document.getElementById("modalQrImg");
    const modalSha256 = document.getElementById("modalSha256");

    let allApps = [];
    let currentCategory = "All";
    let searchQuery = "";

    // Fetch applications index
    fetch("apps.json")
        .then(res => {
            if (!res.ok) throw new Error("apps.json not found");
            return res.json();
        })
        .then(data => {
            allApps = data;
            renderApps();
        })
        .catch(err => {
            appsGrid.innerHTML = `
                <div class="empty-state">
                    <h3>🚀 Welcome to RPDevs APK Vault</h3>
                    <p>No builds indexed yet. Run the CI/CD pipeline or local build runner to generate your applications.</p>
                </div>
            `;
        });

    function renderApps() {
        const filtered = allApps.filter(app => {
            const matchesCat = currentCategory === "All" || 
                               app.category === currentCategory || 
                               (currentCategory.includes("ReVanced") && app.app_name.includes("ReVanced")) ||
                               (currentCategory.includes("Morphe") && app.app_name.includes("Morphe")) ||
                               (currentCategory.includes("Root") && app.is_module);
            
            const matchesSearch = searchQuery === "" ||
                                  app.app_name.toLowerCase().includes(searchQuery) ||
                                  app.package_name.toLowerCase().includes(searchQuery) ||
                                  app.filename.toLowerCase().includes(searchQuery) ||
                                  app.architectures.join(" ").toLowerCase().includes(searchQuery);

            return matchesCat && matchesSearch;
        });

        if (filtered.length === 0) {
            appsGrid.innerHTML = `<div class="empty-state"><p>No matching applications found.</p></div>`;
            return;
        }

        appsGrid.innerHTML = filtered.map(app => `
            <div class="app-card">
                <div>
                    <div class="app-card-header">
                        <div class="app-icon">${app.is_module ? "📦" : "📱"}</div>
                        <div class="app-info">
                            <h3>${app.app_name}</h3>
                            <div class="app-package">${app.package_name}</div>
                        </div>
                    </div>
                    <div class="app-meta-badges">
                        <span class="badge badge-version">v${app.version_name}</span>
                        <span class="badge badge-arch">${app.architectures.join(", ")}</span>
                        <span class="badge">${app.size_mb || (app.size_bytes / (1024*1024)).toFixed(1)} MB</span>
                    </div>
                </div>
                <div class="app-card-actions">
                    <a href="${app.download_url}" class="btn btn-primary" download>
                        ⬇ Download
                    </a>
                    <button class="btn btn-secondary qr-btn" data-title="${app.app_name}" data-qr="${app.qr_code_url}" data-sha="${app.sha256}">
                        📱 QR
                    </button>
                </div>
            </div>
        `).join("");

        // Attach modal triggers
        document.querySelectorAll(".qr-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                modalAppTitle.textContent = btn.dataset.title;
                modalQrImg.src = btn.dataset.qr;
                modalSha256.textContent = btn.dataset.sha;
                qrModal.classList.add("active");
            });
        });
    }

    // Category click
    categoryButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            categoryButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentCategory = btn.dataset.category;
            renderApps();
        });
    });

    // Search input
    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderApps();
    });

    // Modal close
    closeModalBtn.addEventListener("click", () => qrModal.classList.remove("active"));
    qrModal.addEventListener("click", (e) => {
        if (e.target === qrModal) qrModal.classList.remove("active");
    });
});
