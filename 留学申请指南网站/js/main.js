// 主要的网站功能JavaScript文件

class StudyAbroadGuide {
    constructor() {
        this.currentSection = '';
        this.searchResults = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadContent();
        this.setupSearch();
        this.setupNavigation();
        this.setupScrollSpy();
        this.setupResponsive();
        this.setupAnimations();
    }

    setupEventListeners() {
        // 移动端菜单按钮
        const menuBtn = document.querySelector('.mobile-menu-btn');
        if (menuBtn) {
            menuBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // 遮罩层点击
        const overlay = document.getElementById('sidebarOverlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.toggleSidebar());
        }

        // 窗口大小变化
        window.addEventListener('resize', () => this.handleResize());

        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (sidebar && overlay) {
            if (sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
                overlay.classList.add('hidden');
            } else {
                sidebar.classList.add('show');
                overlay.classList.remove('hidden');
            }
        }
    }

    handleResize() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (window.innerWidth >= 768) {
            if (sidebar) sidebar.classList.remove('show');
            if (overlay) overlay.classList.add('hidden');
        }
    }

    handleKeyboard(e) {
        // ESC 键关闭侧边栏
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('show')) {
                this.toggleSidebar();
            }
        }

        // Ctrl+F 聚焦搜索框
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }
    }

    loadContent() {
        this.loadPart1Content();
        this.loadPart2Content();
    }

    loadPart1Content() {
        if (typeof guideContent === 'undefined') {
            console.error('Guide content not loaded');
            return;
        }

        const part1Container = document.querySelector('#part1 .bg-white');
        if (!part1Container) return;

        // 清除现有内容（保留标题部分）
        const existingContent = part1Container.querySelector('.border-l-4').parentElement;
        const sectionsContainer = document.createElement('div');
        
        guideContent.part1.sections.forEach(section => {
            const sectionDiv = document.createElement('div');
            sectionDiv.id = section.id;
            sectionDiv.className = 'content-section mb-10';
            
            sectionDiv.innerHTML = `
                <h3 class="text-lg sm:text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <i class="${section.icon} text-primary-600 mr-3"></i>
                    ${section.title}
                </h3>
                <div class="prose max-w-none">
                    ${section.content}
                </div>
            `;
            
            sectionsContainer.appendChild(sectionDiv);
        });

        part1Container.appendChild(sectionsContainer);
    }

    loadPart2Content() {
        if (typeof guideContent === 'undefined') {
            console.error('Guide content not loaded');
            return;
        }

        const countryContent = document.getElementById('countryContent');
        if (!countryContent) return;

        guideContent.part2.countries.forEach(country => {
            const countryDiv = document.createElement('div');
            countryDiv.id = country.id;
            countryDiv.className = 'content-section mb-8';
            
            countryDiv.innerHTML = `
                <h3 class="text-lg sm:text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <i class="${country.icon} text-primary-600 mr-3"></i>
                    ${country.name}
                </h3>
                ${country.content}
            `;
            
            countryContent.appendChild(countryDiv);
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });

        // 清除搜索
        searchInput.addEventListener('focus', () => {
            if (searchInput.value === '') {
                this.clearSearch();
            }
        });
    }

    performSearch(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) {
            this.clearSearch();
            return;
        }

        this.clearSearch();
        
        const lowerSearchTerm = searchTerm.toLowerCase();
        const mainContent = document.querySelector('.main-content');
        
        // 查找所有文本节点
        const walker = document.createTreeWalker(
            mainContent,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    // 跳过导航、按钮等元素
                    const parent = node.parentElement;
                    if (parent.closest('.sidebar') || 
                        parent.closest('nav') || 
                        parent.closest('button') ||
                        parent.closest('input')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return node.textContent.toLowerCase().includes(lowerSearchTerm) 
                        ? NodeFilter.FILTER_ACCEPT 
                        : NodeFilter.FILTER_REJECT;
                }
            },
            false
        );

        const matchingNodes = [];
        let node;
        while (node = walker.nextNode()) {
            matchingNodes.push(node);
        }

        // 高亮匹配的文本
        matchingNodes.forEach(textNode => {
            const text = textNode.textContent;
            const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
            
            if (regex.test(text)) {
                const highlightedHTML = text.replace(regex, '<mark class="highlight bg-yellow-300 px-1 rounded">$1</mark>');
                const wrapper = document.createElement('span');
                wrapper.innerHTML = highlightedHTML;
                textNode.parentNode.replaceChild(wrapper, textNode);
            }
        });

        // 滚动到第一个匹配项
        const firstHighlight = document.querySelector('.highlight');
        if (firstHighlight) {
            firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // 显示搜索结果数量
        const highlightCount = document.querySelectorAll('.highlight').length;
        this.showSearchResults(highlightCount, searchTerm);
    }

    clearSearch() {
        // 移除所有高亮
        const highlights = document.querySelectorAll('.highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });

        // 移除搜索结果提示
        this.hideSearchResults();
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    showSearchResults(count, term) {
        // 可以在这里添加搜索结果提示
        console.log(`Found ${count} matches for "${term}"`);
    }

    hideSearchResults() {
        // 隐藏搜索结果提示
    }

    setupNavigation() {
        // 设置所有导航链接
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                this.scrollToSection(targetId);
                this.setActiveNavLink(link);
                
                // 移动端关闭侧边栏
                if (window.innerWidth < 768) {
                    this.toggleSidebar();
                }
            });
        });

        // 设置国家卡片点击
        document.querySelectorAll('.country-card').forEach(card => {
            card.addEventListener('click', () => {
                const targetId = card.getAttribute('onclick').match(/scrollToSection\('(.+?)'\)/)?.[1];
                if (targetId) {
                    this.scrollToSection(targetId);
                }
            });
        });
    }

    scrollToSection(sectionId) {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
            this.currentSection = sectionId;
        }
    }

    setActiveNavLink(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    setupScrollSpy() {
        const sections = document.querySelectorAll('[id^="section"], [id^="part"]');
        
        const observerOptions = {
            root: null,
            rootMargin: '-20% 0px -70% 0px',
            threshold: 0
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.id;
                    const navLink = document.querySelector(`[href="#${id}"]`);
                    if (navLink) {
                        this.setActiveNavLink(navLink);
                    }
                    this.currentSection = id;
                }
            });
        }, observerOptions);

        sections.forEach(section => {
            observer.observe(section);
        });
    }

    setupResponsive() {
        // 处理图片懒加载
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            imageObserver.unobserve(img);
                        }
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    setupAnimations() {
        // 滚动动画
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    animationObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        // 为新添加的内容设置动画
        setTimeout(() => {
            document.querySelectorAll('.content-section').forEach(section => {
                if (!section.classList.contains('fade-in-up')) {
                    animationObserver.observe(section);
                }
            });
        }, 100);
    }

    // 公共方法：外部调用
    static scrollToSection(sectionId) {
        const guide = window.studyGuide;
        if (guide) {
            guide.scrollToSection(sectionId);
        }
    }

    // 打印功能
    print() {
        // 打印前的准备
        const originalTitle = document.title;
        document.title = '本科生国外留学申请全流程指南';
        
        // 触发打印
        window.print();
        
        // 恢复标题
        document.title = originalTitle;
    }

    // 获取当前章节信息
    getCurrentSection() {
        return this.currentSection;
    }

    // 获取所有章节列表
    getAllSections() {
        const sections = [];
        document.querySelectorAll('[id^="section"], [id^="part"]').forEach(section => {
            const title = section.querySelector('h2, h3')?.textContent;
            if (title) {
                sections.push({
                    id: section.id,
                    title: title.trim()
                });
            }
        });
        return sections;
    }
}

// 全局函数（向后兼容）
function scrollToSection(sectionId) {
    StudyAbroadGuide.scrollToSection(sectionId);
}

function toggleSidebar() {
    if (window.studyGuide) {
        window.studyGuide.toggleSidebar();
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    window.studyGuide = new StudyAbroadGuide();
    
    // 为打印按钮添加事件
    const printBtn = document.querySelector('button[onclick="window.print()"]');
    if (printBtn) {
        printBtn.onclick = () => window.studyGuide.print();
    }
});

// 防止意外离开页面
window.addEventListener('beforeunload', function(e) {
    // 只在用户有输入搜索内容时提示
    const searchInput = document.getElementById('searchInput');
    if (searchInput && searchInput.value.trim()) {
        e.preventDefault();
        e.returnValue = '';
    }
});
