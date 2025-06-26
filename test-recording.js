const { chromium } = require('playwright');

(async () => {
  // Launch the browser
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  // Create a new context with recording options
  const context = await browser.newContext({
    recordVideo: {
      dir: './recordings',
      size: { width: 1280, height: 720 }
    }
  });
  
  // Create a new page
  const page = await context.newPage();
  
  try {
    // Start the backend server
    console.log('Starting backend server...');
    
    // Navigate to the login page
    await page.goto('http://localhost:3000/auth/login');
    console.log('Navigated to login page');
    
    // Wait for the page to load
    await page.waitForSelector('form', { timeout: 10000 });
    
    // Login with test credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');
    console.log('Logged in');
    
    // Wait for redirect to projects page
    await page.waitForURL('**/projects', { timeout: 10000 });
    console.log('Redirected to projects page');
    
    // Create a new project
    await page.click('text=New Project');
    await page.fill('input[placeholder="Project Name"]', 'High-Rise Building Project');
    await page.fill('textarea', 'A 15-story building design and analysis project');
    await page.click('button:has-text("Create Project")');
    console.log('Created new project');
    
    // Wait for the project to be created and click on it
    await page.waitForSelector('text=High-Rise Building Project', { timeout: 5000 });
    await page.click('text=High-Rise Building Project');
    console.log('Opened project');
    
    // Create a new model
    await page.click('text=New Model');
    await page.fill('input[placeholder="Model Name"]', '15-Story Building Model');
    await page.fill('textarea', 'Structural model for a 15-story building');
    await page.click('button:has-text("Create Model")');
    console.log('Created new model');
    
    // Wait for the model to be created and click on it
    await page.waitForSelector('text=15-Story Building Model', { timeout: 5000 });
    await page.click('text=15-Story Building Model');
    console.log('Opened model');
    
    // Wait for the 3D viewer to load
    await page.waitForSelector('canvas', { timeout: 10000 });
    console.log('3D viewer loaded');
    
    // Open the NLP prompt
    await page.click('button >> svg[data-testid="MessageCircleIcon"]');
    console.log('Opened NLP prompt');
    
    // Use NLP to create a 15-story building
    await page.fill('textarea', 'Create a 15-story building');
    await page.click('button >> svg[data-testid="SendIcon"]');
    console.log('Sent NLP prompt to create 15-story building');
    
    // Wait for the building to be created (this might take some time)
    await page.waitForTimeout(5000);
    
    // Add more NLP commands
    const commands = [
      'Add loads to the structure',
      'Design the columns for the building',
      'Design the beams for the building',
      'Create detailed drawings of the structure'
    ];
    
    for (const command of commands) {
      // Clear previous text and enter new command
      await page.fill('textarea', command);
      await page.click('button >> svg[data-testid="SendIcon"]');
      console.log(`Sent NLP prompt: ${command}`);
      
      // Wait for processing
      await page.waitForTimeout(3000);
    }
    
    // Interact with the 3D model
    const canvas = await page.$('canvas');
    
    // Rotate the model
    const canvasBoundingBox = await canvas.boundingBox();
    const centerX = canvasBoundingBox.x + canvasBoundingBox.width / 2;
    const centerY = canvasBoundingBox.y + canvasBoundingBox.height / 2;
    
    await page.mouse.move(centerX, centerY);
    await page.mouse.down();
    await page.mouse.move(centerX + 100, centerY);
    await page.mouse.move(centerX + 200, centerY + 100);
    await page.mouse.up();
    console.log('Rotated the 3D model');
    
    // Zoom in and out
    await page.mouse.move(centerX, centerY);
    await page.mouse.wheel(0, -100); // Zoom in
    await page.waitForTimeout(1000);
    await page.mouse.wheel(0, 200); // Zoom out
    console.log('Zoomed in and out of the 3D model');
    
    // Wait a bit to see the final result
    await page.waitForTimeout(5000);
    
    console.log('Test completed successfully');
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    // Close the browser
    await context.close();
    await browser.close();
  }
})();