import { test, expect } from '@playwright/test';

test('Design a 15-story building using NLP', async ({ page }) => {
  // Go to the homepage
  await page.goto('http://localhost:3000');
  
  // Take a screenshot of the homepage
  await page.screenshot({ path: 'screenshots/01-homepage.png' });
  
  // Check if the application is running
  const title = await page.title();
  console.log(`Page title: ${title}`);
  
  // Check if we can access the API
  const apiResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      return await response.json();
    } catch (error) {
      return { error: error.message };
    }
  });
  
  console.log('API Health Response:', apiResponse);
  
  // Create a simple NLP prompt for a 15-story building
  const nlpPrompt = `
    Create a 15-story office building with the following specifications:
    - Regular rectangular floor plan of 30m x 20m
    - Story height of 3.5m for all floors
    - Reinforced concrete structure with columns spaced at 5m in both directions
    - Core walls around elevator and staircase at the center
    - Flat slab system with 250mm thickness
    - Columns with 600mm x 600mm cross-section
    - Core walls with 300mm thickness
    - Design for office live load of 3 kN/m²
    - Wind load as per ASCE 7-16
    - Seismic load as per ASCE 7-16 with site class D
  `;
  
  console.log('NLP Prompt:', nlpPrompt);
  
  // Test the NLP endpoint directly
  const nlpResponse = await page.evaluate(async (prompt) => {
    try {
      const response = await fetch('http://localhost:8000/api/nlp/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          model_id: 1, // Using a default model ID
        }),
      });
      return await response.json();
    } catch (error) {
      return { error: error.message };
    }
  }, nlpPrompt);
  
  console.log('NLP Response:', nlpResponse);
  
  // Take a screenshot of the final state
  await page.screenshot({ path: 'screenshots/02-final.png' });
});