document.getElementById('extractBtn').addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab.url.includes('youtube.com/watch')) {
            document.getElementById('comments').innerHTML = 
                '<p style="color: red;">Please open a YouTube video first!</p>';
            return;
        }

        // Get desired number of comments from input and enforce max limit
        let limit = parseInt(document.getElementById('commentLimit').value) || 10;
        if (limit > 100) {
            limit = 100;
            document.getElementById('commentLimit').value = 100;
            // Show a message about the limit
            document.getElementById('comments').innerHTML = 
                '<p style="color: orange;">Maximum limit is 100 comments. Extracting 100 comments...</p>';
            await new Promise(resolve => setTimeout(resolve, 1500)); // Show message for 1.5 seconds
        }

        // Inject and execute the content script
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: async (desiredComments) => {
                // Extract video information
                const videoInfo = {
                    title: document.querySelector('h1.ytd-video-primary-info-renderer')?.textContent?.trim() || 'Unknown Title',
                    viewCount: document.querySelector('#count .ytd-video-view-count-renderer')?.textContent?.trim() || 'Unknown views',
                    likeCount: (() => {
                        // Try to find the like button with the new structure
                        const selectors = [
                            // New YouTube structure (segmented button)
                            'ytd-segmented-like-dislike-button-renderer #segmented-like-button button',
                            // Alternative paths
                            'ytd-menu-renderer ytd-segmented-like-dislike-button-renderer button[aria-label*="like this video"]',
                            '#top-level-buttons-computed button[aria-label*="like this video"]'
                        ];

                        for (const selector of selectors) {
                            const button = document.querySelector(selector);
                            if (button) {
                                // Try to get the count from aria-label first
                                const ariaLabel = button.getAttribute('aria-label');
                                if (ariaLabel) {
                                    const match = ariaLabel.match(/like this video along with ([\d,]+)/i);
                                    if (match) {
                                        return match[1];
                                    }
                                }
                                
                                // If aria-label doesn't work, try getting the text content
                                const textElement = button.querySelector('#text');
                                if (textElement) {
                                    const text = textElement.textContent.trim();
                                    if (text && text !== 'Like') {
                                        return text;
                                    }
                                }
                            }
                        }

                        // Fallback: try to find it in the video data
                        const videoData = document.querySelector('ytd-watch-flexy');
                        if (videoData) {
                            const likeStatus = videoData.getAttribute('like-button-state');
                            if (likeStatus) {
                                try {
                                    const data = JSON.parse(likeStatus);
                                    if (data && data.title) {
                                        return data.title;
                                    }
                                } catch (e) {
                                    console.error('Error parsing like button state:', e);
                                }
                            }
                        }

                        return 'Unknown likes';
                    })(),
                    uploadDate: document.querySelector('#info-strings yt-formatted-string')?.textContent?.trim() || 'Unknown date',
                    channelName: document.querySelector('#channel-name a')?.textContent?.trim() || 'Unknown channel',
                    channelSubs: document.querySelector('#owner-sub-count')?.textContent?.trim() || 'Unknown subscribers',
                    // Update channel avatar selector to match YouTube's structure
                    channelAvatar: (() => {
                        const selectors = [
                            '#channel-thumbnail img.yt-img-shadow',
                            '#owner #avatar img',
                            '#owner-sub-count img',
                            'ytd-video-owner-renderer img.yt-img-shadow'
                        ];

                        for (const selector of selectors) {
                            const img = document.querySelector(selector);
                            if (img && img.src) {
                                // Get the highest quality version by modifying the URL
                                return img.src.replace('s48-c-k', 's100-c-k'); // Increase size to 100px
                            }
                        }
                        return null;
                    })()
                };

                const comments = [];
                let attempts = 0;
                const maxAttempts = 30;
                let lastCommentCount = 0;
                let noNewCommentsCount = 0;

                // First scroll to comments section
                const commentsSection = document.querySelector('#comments');
                if (commentsSection) {
                    commentsSection.scrollIntoView({ behavior: 'smooth' });
                    // Wait for initial load
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }

                const scrollAndWait = async () => {
                    // Scroll in smaller increments
                    const currentPosition = window.scrollY;
                    const increment = 1000; // Scroll 1000px at a time
                    window.scrollBy(0, increment);
                    
                    // Add a small random delay to mimic human behavior
                    const randomDelay = Math.floor(Math.random() * 500) + 1500;
                    await new Promise(resolve => setTimeout(resolve, randomDelay));
                };

                while (comments.length < desiredComments && attempts < maxAttempts) {
                    // Get comment threads
                    const commentThreads = document.querySelectorAll('ytd-comment-thread-renderer');
                    
                    commentThreads.forEach(thread => {
                        if (comments.length < desiredComments) {
                            const commentElement = thread.querySelector('#content-text');
                            const timeElement = thread.querySelector('a.yt-simple-endpoint[href*="lc="]');
                            const likeElement = thread.querySelector('#vote-count-middle');
                            const authorElement = thread.querySelector('#author-text');
                            
                            if (commentElement) {
                                const commentText = commentElement.textContent.trim();
                                const timestamp = timeElement ? timeElement.textContent.trim() : 'Unknown time';
                                const likes = likeElement ? likeElement.textContent.trim() : '0';
                                const author = authorElement ? authorElement.textContent.trim() : 'Unknown author';

                                const isDuplicate = comments.some(c => 
                                    c.text === commentText && 
                                    c.author === author && 
                                    c.timestamp === timestamp
                                );

                                if (commentText && !isDuplicate) {
                                    comments.push({
                                        text: commentText,
                                        timestamp: timestamp,
                                        likes: likes,
                                        author: author
                                    });
                                }
                            }
                        }
                    });

                    if (comments.length === lastCommentCount) {
                        noNewCommentsCount++;
                        if (noNewCommentsCount >= 5) {
                            break;
                        }
                    } else {
                        noNewCommentsCount = 0;
                    }
                    lastCommentCount = comments.length;

                    if (comments.length < desiredComments) {
                        await scrollAndWait();
                        
                        if (attempts % 5 === 0) {
                            window.scrollBy(0, -500);
                            await new Promise(resolve => setTimeout(resolve, 1000));
                            window.scrollBy(0, 500);
                            await new Promise(resolve => setTimeout(resolve, 1000));
                        }
                        
                        attempts++;
                    } else {
                        break;
                    }
                }

                // Scroll back to top smoothly
                window.scrollTo({ top: 0, behavior: 'smooth' });

                return {
                    videoInfo,
                    comments: comments.slice(0, desiredComments),
                    totalFound: comments.length,
                    reachedLimit: attempts >= maxAttempts,
                    attempts: attempts
                };
            },
            args: [limit]
        });

        const { videoInfo, comments, totalFound, reachedLimit, attempts } = results[0].result;
        displayVideoInfo(videoInfo);
        displayComments(comments, totalFound, reachedLimit, attempts);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('comments').innerHTML = 
            `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// Add new function to display video information
function displayVideoInfo(videoInfo) {
    const commentsDiv = document.getElementById('comments');
    commentsDiv.innerHTML = '';

    const videoInfoDiv = document.createElement('div');
    videoInfoDiv.className = 'video-info';
    
    // Create channel header with avatar and info
    const channelHeader = document.createElement('div');
    channelHeader.className = 'channel-header';
    
    // Improved avatar handling
    const avatarHtml = videoInfo.channelAvatar 
        ? `<img src="${videoInfo.channelAvatar}" 
             class="channel-avatar" 
             alt="${videoInfo.channelName}'s avatar"
             onerror="this.onerror=null; this.src='default-avatar.png';">`
        : '<div class="channel-avatar-placeholder"></div>';
        
    channelHeader.innerHTML = `
        ${avatarHtml}
        <div class="channel-info">
            <div class="channel-name">${videoInfo.channelName}</div>
            <div class="channel-subs">${videoInfo.channelSubs}</div>
        </div>
    `;

    // Create video details section
    const videoDetails = document.createElement('div');
    videoDetails.className = 'video-details';
    videoDetails.innerHTML = `
        <h2 class="video-title">${videoInfo.title}</h2>
        <div class="video-stats">
            <span>${videoInfo.viewCount}</span>
            <span>•</span>
            <span>${videoInfo.uploadDate}</span>
            <span>•</span>
            <span>${videoInfo.likeCount} likes</span>
        </div>
        <hr class="separator">
    `;

    videoInfoDiv.appendChild(channelHeader);
    videoInfoDiv.appendChild(videoDetails);
    commentsDiv.appendChild(videoInfoDiv);
}

// Update existing displayComments function
function displayComments(comments, totalFound, reachedLimit, attempts) {
    const commentsDiv = document.getElementById('comments');
    
    if (!comments || comments.length === 0) {
        commentsDiv.innerHTML += `
            <p>No comments found. The page might need to load more comments.</p>
            <p>Try scrolling down the page and clicking Extract again.</p>
        `;
        return;
    }

    // Add comment count and status
    const countDiv = document.createElement('div');
    countDiv.className = 'comments-header';
    
    let statusMessage = `Found ${comments.length} comments`;
    if (reachedLimit) {
        statusMessage += ` (reached maximum scroll attempts after ${attempts} scrolls, found ${totalFound} total comments)`;
    } else if (totalFound > comments.length) {
        statusMessage += ` (showing ${comments.length} of ${totalFound} found)`;
    }
    countDiv.textContent = statusMessage;
    commentsDiv.appendChild(countDiv);

    comments.forEach(comment => {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment';
        
        // Create metadata section
        const metaDiv = document.createElement('div');
        metaDiv.style.fontSize = '12px';
        metaDiv.style.color = '#666';
        metaDiv.style.marginBottom = '5px';
        metaDiv.innerHTML = `
            <strong>${comment.author}</strong> • 
            ${comment.timestamp} • 
            ${comment.likes} likes
        `;
        
        // Create comment text section
        const textDiv = document.createElement('div');
        textDiv.textContent = comment.text;
        
        commentDiv.appendChild(metaDiv);
        commentDiv.appendChild(textDiv);
        commentsDiv.appendChild(commentDiv);
    });
}
