document.addEventListener("DOMContentLoaded", function() {
    const userMenu = document.getElementById("jazzy-usermenu");
    if (userMenu) {
        let customLink = null;
        let customDivider = null;
        
        for (let i = 0; i < userMenu.children.length; i++) {
            let el = userMenu.children[i];
            if (el.tagName === 'A' && el.textContent.includes('UserAdmin')) {
                customLink = el;
                if (i > 0 && userMenu.children[i-1].classList.contains('dropdown-divider')) {
                    customDivider = userMenu.children[i-1];
                }
                break;
            }
        }
        
        if (customLink) {
            const changePasswordLink = userMenu.querySelector('a[href*="password_change"]');
            if (changePasswordLink) {
                userMenu.insertBefore(customLink, changePasswordLink);
                if (customDivider) {
                    userMenu.insertBefore(customDivider, changePasswordLink);
                }
            }
        }
    }
});
