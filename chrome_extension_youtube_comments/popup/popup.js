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
                // This function runs in the context of the web page
                const comments = [];
                let attempts = 0;
                const maxAttempts = 30; // Increased max attempts
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
                            // Updated timestamp selector to match YouTube's structure
                            const timeElement = thread.querySelector('a.yt-simple-endpoint[href*="lc="]');
                            const likeElement = thread.querySelector('#vote-count-middle');
                            const authorElement = thread.querySelector('#author-text');
                            
                            if (commentElement) {
                                const commentText = commentElement.textContent.trim();
                                // Extract timestamp from the link element
                                const timestamp = timeElement ? timeElement.textContent.trim() : 'Unknown time';
                                const likes = likeElement ? likeElement.textContent.trim() : '0';
                                const author = authorElement ? authorElement.textContent.trim() : 'Unknown author';

                                // Check if this comment is already included
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
                        // If no new comments after 5 attempts, stop trying
                        if (noNewCommentsCount >= 5) {
                            break;
                        }
                    } else {
                        noNewCommentsCount = 0;
                    }
                    lastCommentCount = comments.length;

                    // Always scroll if we haven't reached the desired count
                    if (comments.length < desiredComments) {
                        await scrollAndWait();
                        
                        // Every 5 attempts, try scrolling back up a bit to trigger loading
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

                // Return only the desired number of comments
                return {
                    comments: comments.slice(0, desiredComments),
                    totalFound: comments.length,
                    reachedLimit: attempts >= maxAttempts,
                    attempts: attempts
                };
            },
            args: [limit]  // Using the potentially adjusted limit
        });

        const { comments, totalFound, reachedLimit, attempts } = results[0].result;
        displayComments(comments, totalFound, reachedLimit, attempts);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('comments').innerHTML = 
            `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

function displayComments(comments, totalFound, reachedLimit, attempts) {
    const commentsDiv = document.getElementById('comments');
    commentsDiv.innerHTML = '';
    
    if (!comments || comments.length === 0) {
        commentsDiv.innerHTML = `
            <p>No comments found. The page might need to load more comments.</p>
            <p>Try scrolling down the page and clicking Extract again.</p>
        `;
        return;
    }

    // Add comment count and status
    const countDiv = document.createElement('div');
    countDiv.style.padding = '8px';
    countDiv.style.borderBottom = '2px solid #eee';
    countDiv.style.fontWeight = 'bold';
    
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
