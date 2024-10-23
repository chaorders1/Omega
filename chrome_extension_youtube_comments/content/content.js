// Rate limiting and anti-throttling configurations
const SCROLL_DELAY_MS = 2000 + Math.random() * 1000; // Random delay between 2-3 seconds
const SCROLL_BATCH_SIZE = 5; // Number of scrolls before pause
const BATCH_PAUSE_MS = 5000; // Pause duration between batches
const MAX_COMMENTS_PER_BATCH = 20; // Maximum comments to process in one batch

// Function to extract channel information
function getChannelInfo() {
    try {
        // Try multiple selectors to find channel name
        const selectors = [
            'ytd-channel-name yt-formatted-string.ytd-channel-name a',
            '#channel-name yt-formatted-string a',
            '#owner #text a',
            'ytd-video-owner-renderer .ytd-channel-name a'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent) {
                return {
                    channelName: element.textContent.trim(),
                    channelUrl: element.href
                };
            }
        }

        // Fallback method using structured data
        const structuredData = document.querySelector('script[type="application/ld+json"]');
        if (structuredData) {
            const data = JSON.parse(structuredData.textContent);
            if (data.author) {
                return {
                    channelName: data.author.name,
                    channelUrl: data.author.url
                };
            }
        }

        throw new Error('Channel information not found');
    } catch (error) {
        console.error('Error extracting channel info:', error);
        return {
            channelName: 'Unknown Channel',
            channelUrl: null,
            error: error.message
        };
    }
}

// Listen for messages from popup or background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getChannelInfo') {
        const channelInfo = getChannelInfo();
        sendResponse(channelInfo);
    } else if (request.action === 'autoReply') {
        autoReplyToComments(request.replyLimit, request.replyMessage)
            .then(results => sendResponse(results))
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }
    return true; // Keep the message channel open for async response
});

// Observe DOM changes to handle dynamic loading
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        if (mutation.type === 'childList' && document.querySelector('ytd-channel-name')) {
            observer.disconnect();
            break;
        }
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

async function extractCommentsWithRateLimit(desiredComments) {
    const comments = [];
    let attempts = 0;
    const maxAttempts = 30;
    let lastCommentCount = 0;
    let noNewCommentsCount = 0;

    // Add random delays between operations
    const randomDelay = () => new Promise(resolve => 
        setTimeout(resolve, Math.random() * 1000 + 500)
    );

    // Scroll with rate limiting
    const scrollWithRateLimit = async () => {
        for (let i = 0; i < SCROLL_BATCH_SIZE; i++) {
            if (comments.length >= desiredComments) break;

            window.scrollBy(0, Math.floor(500 + Math.random() * 300));
            await new Promise(resolve => setTimeout(resolve, SCROLL_DELAY_MS));
            
            // Add some random mouse movements to appear more human-like
            simulateHumanBehavior();
        }
        
        // Pause between batches
        await new Promise(resolve => setTimeout(resolve, BATCH_PAUSE_MS));
    };

    // Simulate human-like behavior
    const simulateHumanBehavior = () => {
        const randomX = Math.floor(Math.random() * window.innerWidth);
        const randomY = Math.floor(Math.random() * window.innerHeight);
        
        // Create and dispatch a mouse move event
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: randomX,
            clientY: randomY,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(mouseEvent);
    };

    try {
        // Initial delay before starting
        await randomDelay();

        while (comments.length < desiredComments && attempts < maxAttempts) {
            const commentThreads = document.querySelectorAll('ytd-comment-thread-renderer');
            let newCommentsInBatch = 0;

            for (const thread of commentThreads) {
                if (comments.length >= desiredComments || 
                    newCommentsInBatch >= MAX_COMMENTS_PER_BATCH) break;

                const commentData = extractCommentData(thread);
                if (commentData && !isDuplicate(comments, commentData)) {
                    comments.push(commentData);
                    newCommentsInBatch++;
                    
                    // Add small delay between processing comments
                    await randomDelay();
                }
            }

            if (comments.length === lastCommentCount) {
                noNewCommentsCount++;
                if (noNewCommentsCount >= 3) {
                    break;
                }
            } else {
                noNewCommentsCount = 0;
            }
            
            lastCommentCount = comments.length;

            if (comments.length < desiredComments) {
                await scrollWithRateLimit();
                attempts++;
            }
        }

        // Smooth scroll back to top
        await smoothScrollToTop();

        return {
            comments: comments.slice(0, desiredComments),
            totalFound: comments.length,
            reachedLimit: attempts >= maxAttempts,
            attempts: attempts
        };

    } catch (error) {
        console.error('Error in comment extraction:', error);
        return {
            comments: comments.slice(0, desiredComments),
            totalFound: comments.length,
            error: error.message,
            attempts: attempts
        };
    }
}

function extractCommentData(thread) {
    try {
        const commentElement = thread.querySelector('#content-text');
        const timeElement = thread.querySelector('a.yt-simple-endpoint[href*="lc="]');
        const likeElement = thread.querySelector('#vote-count-middle');
        const authorElement = thread.querySelector('#author-text');
        
        if (!commentElement) return null;

        return {
            text: commentElement.textContent.trim(),
            timestamp: timeElement ? timeElement.textContent.trim() : 'Unknown time',
            likes: likeElement ? likeElement.textContent.trim() : '0',
            author: authorElement ? authorElement.textContent.trim() : 'Unknown author'
        };
    } catch (error) {
        console.error('Error extracting comment data:', error);
        return null;
    }
}

function isDuplicate(comments, newComment) {
    return comments.some(c => 
        c.text === newComment.text && 
        c.author === newComment.author && 
        c.timestamp === newComment.timestamp
    );
}

async function smoothScrollToTop() {
    const scrollStep = -window.scrollY / 20;
    const scrollInterval = setInterval(() => {
        if (window.scrollY !== 0) {
            window.scrollBy(0, scrollStep);
        } else {
            clearInterval(scrollInterval);
        }
    }, 15);
    
    return new Promise(resolve => {
        setTimeout(resolve, 500);
    });
}

// Add this function for auto-scrolling to comments section
async function scrollToComments() {
    // First scroll to comments section
    const commentsSection = document.querySelector('#comments');
    if (!commentsSection) {
        throw new Error('Comments section not found');
    }

    // Scroll to comments section smoothly
    commentsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Scroll a bit to load more comments
    for (let i = 0; i < 3; i++) {
        window.scrollBy(0, 500);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Scroll back to comments section
    commentsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await new Promise(resolve => setTimeout(resolve, 1000));
}

// Update the autoReplyToComments function
async function autoReplyToComments(replyLimit, replyMessage) {
    const results = {
        successful: 0,
        failed: 0,
        skipped: 0,
        total: replyLimit,
        errors: []
    };

    try {
        // First scroll to load comments
        await scrollToComments();

        // Get all comment threads
        const commentThreads = document.querySelectorAll('ytd-comment-thread-renderer');
        let processedCount = 0;
        let checkedCount = 0;

        for (const thread of commentThreads) {
            if (processedCount >= replyLimit) break;
            checkedCount++;

            try {
                // Check if we've already replied to this comment
                const myReplies = thread.querySelectorAll('ytd-comment-renderer.ytd-comment-replies-renderer');
                const channelName = document.querySelector('#channel-name yt-formatted-string')?.textContent?.trim();
                let alreadyReplied = false;

                // Check each reply to see if it's from the current user
                for (const reply of myReplies) {
                    const replyAuthor = reply.querySelector('#author-text')?.textContent?.trim();
                    if (replyAuthor === channelName) {
                        alreadyReplied = true;
                        break;
                    }
                }

                if (alreadyReplied) {
                    results.skipped++;
                    console.log('Skipping comment - already replied');
                    continue;
                }

                // Find and click the reply button
                const replyButton = thread.querySelector('#reply-button-end button');
                if (!replyButton) {
                    throw new Error('Reply button not found');
                }

                // Click reply and wait for input to appear
                replyButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));

                // Find the reply input
                const replyInput = thread.querySelector('#contenteditable-root');
                if (!replyInput) {
                    throw new Error('Reply input not found');
                }

                // Set reply text and trigger input event
                replyInput.textContent = replyMessage;
                replyInput.dispatchEvent(new Event('input', { bubbles: true }));
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Find and click submit button
                const submitButton = thread.querySelector('#submit-button button');
                if (!submitButton) {
                    throw new Error('Submit button not found');
                }

                submitButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));

                results.successful++;
                processedCount++;

                // Report progress with skipped count
                chrome.runtime.sendMessage({
                    action: 'updateReplyProgress',
                    progress: {
                        current: processedCount,
                        total: replyLimit,
                        successful: results.successful,
                        failed: results.failed,
                        skipped: results.skipped,
                        checked: checkedCount
                    }
                });

                // Add random delay between replies (2-4 seconds)
                await new Promise(resolve => 
                    setTimeout(resolve, 2000 + Math.random() * 2000)
                );

            } catch (error) {
                results.failed++;
                results.errors.push(`Failed to reply to comment: ${error.message}`);
                
                // Try to cancel/close reply if error occurs
                try {
                    const cancelButton = thread.querySelector('#cancel-button');
                    if (cancelButton) cancelButton.click();
                } catch (e) {
                    console.error('Error canceling reply:', e);
                }
                
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        // When complete, add completion status
        results.completed = true;
        results.completionTime = new Date().toLocaleTimeString();

        return results;

    } catch (error) {
        console.error('Auto-reply error:', error);
        results.errors.push(`General error: ${error.message}`);
        results.completed = false;
        return results;
    }
}
