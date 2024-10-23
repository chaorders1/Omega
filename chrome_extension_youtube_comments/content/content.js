// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extractComments') {
        const comments = extractComments();
        sendResponse({ comments });
    }
    return true;
});

function extractComments() {
    const comments = [];
    const commentElements = document.querySelectorAll('ytd-comment-thread-renderer #content-text');
    
    commentElements.forEach(element => {
        const commentText = element.textContent.trim();
        if (commentText) {
            comments.push(commentText);
        }
    });

    return comments;
}

// Auto-scroll function to help load more comments
function autoScroll() {
    window.scrollTo(0, document.body.scrollHeight);
}
