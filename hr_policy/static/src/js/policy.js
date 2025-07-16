/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
console.log('policy');

publicWidget.registry.PolicyWidget = publicWidget.Widget.extend({
    selector: '.policy-content, #policy-description, #categoryFilter',
    events: {
        'change': '_onCategoryChange',
    },
    onBuilt: function () {
        this._super.apply(this, arguments);
        this._setDefaultView(); // Set default view on snippet load
    },

    start: function () {
        console.log('policy widget started');
        this._super.apply(this, arguments);
        this._setupEventListeners();
        this._generateContentTOC();
        this._fetchPolices();
        return this;
    },

    _setupEventListeners: function () {
        const versionSelect = document.getElementById('policy-version-select');
        console.log('versionSelect', versionSelect);
        if (versionSelect) {
            versionSelect.addEventListener('change', this._onVersionChange.bind(this));
        }
    },
    _onCategoryChange: function (ev) {
        const selectedCategory = ev.target.value;
        console.log('Selected category:', selectedCategory);
    
        // Select only the policy cards that have the 'data-category-id' attribute
        const policyCards = document.querySelectorAll('.policy-card');
        console.log('All policy cards:', policyCards);
    
        policyCards.forEach(card => {
            const cardCategoryId = card.getAttribute('data-category-id');
            
            // If the card does not have a valid 'data-category-id', skip it
            if (!cardCategoryId) {
                console.log('Skipping card without data-category-id');
                return;
            }
    
            console.log('cardCategoryId', cardCategoryId);
    
            // Show or hide card based on the selected category
            if (!selectedCategory || cardCategoryId === selectedCategory) {
                card.style.display = ''; // Show card
            } else {
                card.style.display = 'none'; // Hide card
            }
        });
    },    
    _fetchPolices: async function () {
        try {
            const result = await jsonrpc('/get_policy');
            console.log('result', result);
            // Check if the result is an object containing a 'policies' array
            if (Array.isArray(result.policies)) {
                this._renderPolicyCards(result.policies);
            } else {
                console.error('Invalid data format: Expected an array of policies');
            }
        } catch (error) {
            console.error('Error fetching policy data:', error);
        }
    },
    

    _renderPolicyCards: function (policies) {
        const policyGrid = document.getElementById('policyGrid');
        policyGrid.innerHTML = ''; // Clear existing cards

        policies.forEach(policy => {
            const policyCard = document.createElement('div');
            console.log('policy', policy);
            policyCard.className = 'policy-card';
            policyCard.setAttribute('data-category-id', policy.sop_id);
            console.log('policyCard', policyCard);

            policyCard.innerHTML = `
            
            <div class="policy_cards" 
                 style="position: relative;
                        background: linear-gradient(135deg, #1a1a1a 0%, #2d3436 100%);
                        border-radius: 16px;
                        overflow: hidden;
                        transition: all 0.3s ease;" 
                        >
            
                <!-- Glowing Border Effect -->
                <div class="glow-effect"></div>
        
                <!-- Card Content -->
                <div class="card-content position-relative" style="padding: 1.8rem;">
                    <!-- Top Meta Section -->
                    <div class="d-flex justify-content-between align-items-start mb-4">
                        <!-- Version Badge -->
                        <span class="version-chip" 
                              style="background: rgba(164, 194, 59, 0.9);
                                     color: #ffffff;
                                     padding: 0.5rem 1.2rem;
                                     border-radius: 25px;
                                     font-size: 0.9rem;
                                     font-weight: 600;
                                     letter-spacing: 0.5px;">
                            <i class="fa fa-code-fork me-2"></i>
                            v${policy.version}
                        </span>
                        
                        <!-- Category -->
                        <span class="category-tag" 
                              style="background: rgba(255, 255, 255, 0.1);
                                     backdrop-filter: blur(8px);
                                     color: #ffffff;
                                     padding: 0.5rem 1.2rem;
                                     border-radius: 25px;
                                     font-size: 0.85rem;">
                            <i class="fa fa-folder-o me-2"></i>
                            ${policy.sop_category_id}
                        </span>
                    </div>
        
                    <!-- Title Section -->
                    <div class="title-wrapper mb-4" style="position: relative; display: flex; align-items: center;">
                        <div class="accent-bar" 
                             style="width: 3px;
                                    height: 100%;
                                    background: #a4c23b;
                                    position: absolute;
                                    left: -1.8rem;
                                    top: 0;">
                        </div>
                        <h4 style="color: white;
                                   font-family: 'Poppins', sans-serif;
                                   font-weight: 600;
                                   font-size: 1.4rem;
                                   line-height: 1.4;
                                   margin: 0;">
                            ${policy.name}
                        </h4>
                    </div>
        
                    <!-- Date Section -->
                    <div class="date-info d-flex align-items-center mb-4 mt-2" 
                         style="color: rgba(255, 255, 255, 0.7);
                                padding-bottom: 1rem;
                                border-bottom: 1px solid rgba(164, 194, 59, 0.2);">
                        <i class="fa fa-calendar me-2" style="color: #a4c23b;"></i>
                        <span style="font-size: 0.9rem;">Effective From:</span>
                        <span class="ms-2 mb-2 mt-1" style="color: white; font-weight: 500;">
                            ${policy.effective_date}
                        </span>
                    </div>
        
                    <!-- Action Button -->
                    <a href="/hr_policy/${policy.id}" 
                       class="view-policy-btn d-inline-flex align-items-center" 
                       style="background: #a4c23b;
                              color: white;
                              padding: 0.8rem 1.5rem;
                              border-radius: 25px;
                              text-decoration: none;
                              font-weight: 500;
                              font-size: 0.95rem;
                              position: relative;
                              overflow: hidden;">
                        <span class="btn-text">View Policy</span>
                        <i class="fa fa-arrow-right ms-2 btn-icon"></i>
                    </a>
                </div>
            </div>
        `;

            policyGrid.appendChild(policyCard);
        });
    },

    _onVersionChange: async function (ev) {
        const selectElement = ev.target;
        const selectedVersionId = selectElement.value;

        try {
            const result = await jsonrpc(
                '/get_policy_version',
                {
                    version_id: selectedVersionId
                },
            );

            if (result && result.description) {
                const contentDiv = document.getElementById('policy-description');
                if (contentDiv) {
                    contentDiv.innerHTML = result.description;
                    // Regenerate TOC after content update
                    this._generateContentTOC();
                }
            }
        } catch (error) {
            console.error('Error fetching policy data:', error);
        }
    },

    _generateContentTOC: function () {
        const contentDiv = document.getElementById('policy-description');
        const sidebarDiv = document.querySelector('.toc-sidebar .card-body');

        if (!contentDiv || !sidebarDiv) return;

        // Clear existing sidebar content except the title
        const title = sidebarDiv.querySelector('h6');
        sidebarDiv.innerHTML = '';
        if (title) sidebarDiv.appendChild(title);

        // Get all headers from content
        const headers = contentDiv.querySelectorAll('h1, h2, h3, h4, h5, h6');
        if (headers.length === 0) return;

        // Create TOC container
        const tocList = document.createElement('ul');
        tocList.className = 'toc-nav';

        // Track header hierarchy
        const headerStack = [];
        let currentList = tocList;

        headers.forEach((header, index) => {
            // Add ID to header if not present
            if (!header.id) {
                header.id = `section-${index}`;
            }

            const level = parseInt(header.tagName[1]);

            // Handle hierarchy
            while (headerStack.length > 0 && headerStack[headerStack.length - 1] >= level) {
                headerStack.pop();
                console.log('Debug====================================:headerStack', headerStack);
                console.log('Debug====================================:currentList', currentList);
                currentList = currentList.parentElement.parentElement ? currentList.parentElement.parentElement : currentList.parentElement;
            }

            // Create list item
            const li = document.createElement('li');
            li.className = 'nav-item';

            const link = document.createElement('a');
            link.href = `#${header.id}`;
            link.className = 'toc-link';
            link.textContent = header.textContent;

            // Add click handler
            link.addEventListener('click', (e) => {
                e.preventDefault();
                header.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

            li.appendChild(link);

            // Handle nested headers
            if (level > (headerStack[headerStack.length - 1] || 0)) {
                const nestedUl = document.createElement('ul');
                nestedUl.className = 'toc-nav';
                li.appendChild(nestedUl);
                currentList.appendChild(li);
                currentList = nestedUl;
                headerStack.push(level);
            } else {
                currentList.appendChild(li);
            }
        });

        // Add TOC to sidebar
        sidebarDiv.appendChild(tocList);

        // Initialize scroll spy
        this._initScrollSpy(headers);
    },

    _initScrollSpy: function (headers) {
        if (this.observer) {
            this.observer.disconnect();
        }

        this.observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Remove active class and highlight from all headers
                        document.querySelectorAll('.toc-link').forEach(link => link.classList.remove('active'));
                        headers.forEach(header => header.classList.remove('highlight'));

                        // Add active class to current link and highlight to current header
                        const activeLink = document.querySelector(`.toc-link[href="#${entry.target.id}"]`);
                        if (activeLink) {
                            activeLink.classList.add('active');
                            entry.target.classList.add('highlight');
                        }

                        // Smooth scroll to header if it's clicked
                        if (window.location.hash === `#${entry.target.id}`) {
                            entry.target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                });
            },
            {
                rootMargin: '-10% 0px -85% 0px',
                threshold: 0.1
            }
        );

        headers.forEach(header => this.observer.observe(header));

        // Add click handlers for headers
        headers.forEach(header => {
            header.addEventListener('click', () => {
                // Remove highlight from all headers
                headers.forEach(h => h.classList.remove('highlight'));
                // Add highlight to clicked header
                header.classList.add('highlight');
            });
        });
    },

    destroy: function () {
        if (this.observer) {
            this.observer.disconnect();
        }
        this._super.apply(this, arguments);
    },
});

export default publicWidget.registry.PolicyWidget;


