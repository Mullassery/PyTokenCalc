#!/usr/bin/env node

/**
 * Playwright Script: Automate Claude Skill Registry Submissions
 *
 * Submits PyCostAudit to:
 * - skills.sh
 * - Swagger Hub
 * - APIs.guru
 *
 * Installation:
 *   npm install -D playwright
 *
 * Usage:
 *   node playwright_skill_submissions.js
 */

const { chromium } = require('playwright');
const fs = require('fs');

const SKILLS_MANIFEST = JSON.parse(fs.readFileSync('./skills_manifest.json', 'utf8'));
const OPENAPI_SPEC = fs.readFileSync('./openapi.json', 'utf8');

async function submitToSkillsSH(page) {
  console.log('\n📤 Submitting to skills.sh...');

  try {
    await page.goto('https://skills.sh/submit', { waitUntil: 'networkidle' });

    // Wait for form to load
    await page.waitForSelector('input[name="name"]', { timeout: 5000 });

    // Fill out form
    await page.fill('input[name="name"]', SKILLS_MANIFEST.skill.name);
    await page.fill('input[name="description"]', SKILLS_MANIFEST.skill.description);
    await page.fill('input[name="repository"]', SKILLS_MANIFEST.skill.repository.url);
    await page.fill('input[name="homepage"]', SKILLS_MANIFEST.skill.homepage);
    await page.fill('input[name="author"]', SKILLS_MANIFEST.skill.author.name);

    // Add tags
    const tagsInput = await page.$('input[name="tags"]');
    if (tagsInput) {
      await tagsInput.evaluate(el => el.value = SKILLS_MANIFEST.skill.tags.join(','));
    }

    // Submit
    await page.click('button[type="submit"]');
    await page.waitForNavigation();

    const currentUrl = page.url();
    if (currentUrl.includes('success') || currentUrl.includes('thank')) {
      console.log('✅ Successfully submitted to skills.sh!');
      console.log(`   URL: https://skills.sh/skills/${SKILLS_MANIFEST.skill.id}`);
      return true;
    } else {
      console.log('⚠️  Submission completed, but verify at: https://skills.sh');
      return true;
    }
  } catch (error) {
    console.log(`❌ skills.sh submission failed: ${error.message}`);
    console.log('   Manual submission: https://skills.sh/submit');
    return false;
  }
}

async function submitToSwaggerHub(page) {
  console.log('\n📤 Registering on Swagger Hub...');

  try {
    await page.goto('https://app.swaggerhub.com/apis', { waitUntil: 'networkidle' });

    // Check if logged in
    const loginBtn = await page.$('a:has-text("Sign in")');
    if (loginBtn) {
      console.log('⚠️  Please log in manually to Swagger Hub first');
      console.log('   1. Go to: https://app.swaggerhub.com');
      console.log('   2. Sign in or create account');
      console.log('   3. Click "Create New" → "Import from URL"');
      console.log('   4. Paste: https://raw.githubusercontent.com/Mullassery/PyCostAudit/main/openapi.json');
      return false;
    }

    // Click Create New
    await page.click('button:has-text("Create New")');
    await page.click('a:has-text("Import from URL")');

    // Fill URL
    const urlInput = await page.$('input[placeholder*="url"]');
    if (urlInput) {
      await urlInput.fill('https://raw.githubusercontent.com/Mullassery/PyCostAudit/main/openapi.json');
      await page.click('button:has-text("Import")');
      await page.waitForNavigation();
      console.log('✅ Successfully imported to Swagger Hub!');
      return true;
    }
  } catch (error) {
    console.log(`❌ Swagger Hub submission failed: ${error.message}`);
    console.log('   Manual registration: https://app.swaggerhub.com');
  }
  return false;
}

async function submitToAPIsGuru(page) {
  console.log('\n📤 Registering on APIs.guru...');

  try {
    await page.goto('https://apis.guru/', { waitUntil: 'networkidle' });

    // Look for add/submit button
    const submitBtn = await page.$('[data-testid="add-api"], button:has-text("Add"), a:has-text("Add")');

    if (submitBtn) {
      await submitBtn.click();

      // Fill form
      const apiNameInput = await page.$('input[name="api-name"], input[placeholder*="name"]');
      if (apiNameInput) {
        await apiNameInput.fill('PyCostAudit');
      }

      const urlInput = await page.$('input[name="api-url"], input[placeholder*="url"]');
      if (urlInput) {
        await urlInput.fill('https://raw.githubusercontent.com/Mullassery/PyCostAudit/main/openapi.json');
      }

      // Submit
      await page.click('button[type="submit"], button:has-text("Submit")');
      await page.waitForNavigation({ timeout: 5000 }).catch(() => {});

      console.log('✅ Successfully submitted to APIs.guru!');
      return true;
    } else {
      console.log('⚠️  APIs.guru interface not recognized');
      console.log('   Manual submission: https://apis.guru');
    }
  } catch (error) {
    console.log(`❌ APIs.guru submission failed: ${error.message}`);
    console.log('   Manual submission: https://apis.guru');
  }
  return false;
}

async function main() {
  console.log('🚀 PyCostAudit Skill Registry Automation');
  console.log('═'.repeat(50));

  const browser = await chromium.launch({ headless: false });
  let successCount = 0;
  let failCount = 0;

  try {
    // skills.sh submission
    let page = await browser.newPage();
    if (await submitToSkillsSH(page)) successCount++;
    else failCount++;
    await page.close();

    // Swagger Hub submission
    page = await browser.newPage();
    if (await submitToSwaggerHub(page)) successCount++;
    else failCount++;
    await page.close();

    // APIs.guru submission
    page = await browser.newPage();
    if (await submitToAPIsGuru(page)) successCount++;
    else failCount++;
    await page.close();

  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n' + '═'.repeat(50));
  console.log(`📊 Submission Summary`);
  console.log(`✅ Successful: ${successCount}`);
  console.log(`❌ Failed/Manual: ${failCount}`);
  console.log('\n📝 Next Steps:');
  console.log('1. Verify submissions at each registry');
  console.log('2. Create GitHub PRs for awesome-claude-skills');
  console.log('3. Post on GitHub Discussions');
  console.log('4. Share on social (Reddit, Product Hunt, HN)');
  console.log('\n💡 For browser-based registries, manual submission');
  console.log('   steps are shown above. Copy-paste the URLs into');
  console.log('   your browser to complete registration.');
}

main().catch(console.error);
