
function initSidebar() {
    {
        const toggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const content = document.getElementById('content-wrapper');
        const topbar = document.getElementById('topbar');
        const footer = document.getElementById('footer');

        // Toggle sidebar
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('sidebar-collapsed');
            content.classList.toggle('content-collapsed');
            topbar.classList.toggle('topbar-collapsed');
            footer.classList.toggle('footer-collapsed');

            // Store state in localStorage
            const isCollapsed = sidebar.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });

        // Check for saved state
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('sidebar-collapsed');
            content.classList.add('content-collapsed');
            topbar.classList.add('topbar-collapsed');
            footer.classList.add('footer-collapsed');
        }

        // Mobile menu toggle
        const mobileMenuToggle = document.createElement('button');
        mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        mobileMenuToggle.className = 'text-white p-2 rounded-full hover:bg-gray-700 md:hidden';
        mobileMenuToggle.id = 'mobileMenuToggle';

        // Insert mobile toggle button
        const topbarLeft = document.querySelector('.topbar > div');
        topbarLeft.insertBefore(mobileMenuToggle, topbarLeft.firstChild);

        mobileMenuToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            sidebar.classList.toggle('show-mobile');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function (event) {
            if (!sidebar.contains(event.target) && !mobileMenuToggle.contains(event.target)) {
                sidebar.classList.remove('show-mobile');
            }
        });

        // Highlight active menu item
        const currentPath = window.location.pathname;
        document.querySelectorAll('.menu-item').forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    }
}
document.addEventListener('DOMContentLoaded', initSidebar);
