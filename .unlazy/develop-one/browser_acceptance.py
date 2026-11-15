import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path.cwd()/'.unlazy/develop-one'

async def main():
    runtime=json.loads((ROOT/'runtime.json').read_text())
    chain=json.loads((ROOT/'profi-chain.json').read_text())
    base=f"http://127.0.0.1:{runtime['frontend_port']}"
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chromium',headless=True)
        context=await browser.new_context(viewport={'width':1440,'height':1000})
        response=await context.request.post(base+'/api/auth/login',data={
            'identifier':'profi-acceptance@example.com','password':'test-only-long-password-123'})
        assert response.status==200, await response.text()
        tokens=await response.json()
        page=await context.new_page()
        await page.goto(base+'/login')
        await page.evaluate('tokens => {localStorage.setItem("access_token",tokens.access_token);localStorage.setItem("refresh_token",tokens.refresh_token)}',tokens)
        await page.goto(base+'/search?q=iPhone')
        source=chain['catalog']['results'][0]['source']['url']
        product_id=chain['catalog']['results'][0]['id']
        await page.locator(f'a[href="{source}"]').first.wait_for(timeout=60000)
        await page.screenshot(path=str(ROOT/'profi-search.png'),full_page=True)
        await page.locator(f'a[href="/product/{product_id}"]').first.click()
        await page.wait_for_url(f'**/product/{product_id}')
        link=page.locator(f'a[href="{source}"]').first
        await link.wait_for(timeout=60000)
        assert await link.is_visible()
        assert await link.get_attribute('target')=='_blank'
        await page.screenshot(path=str(ROOT/'profi-product.png'),full_page=True)
        # Verify the URL rendered by both UI locations equals the real imported offer.
        assert any(o['url']==source for o in json.loads((ROOT/'profi-browser-live.json').read_text())['offers'])
        report={'search_url':base+'/search?q=iPhone','product_id':product_id,'shop_url':source,
                'search_source_visible':True,'detail_source_visible':True,'shop_link_target':'_blank',
                'screenshots':['profi-search.png','profi-product.png']}
        (ROOT/'browser-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        signup_context=await browser.new_context(viewport={'width':1280,'height':1000})
        signup=await signup_context.new_page()
        payment_posts=[]
        signup.on('request',lambda request: payment_posts.append(request.url) if request.method=='POST' and '/api/payment/' in request.url else None)
        await signup.goto(base+'/register?plan=advanced')
        await signup.locator('#full_name').fill('Plan acceptance')
        await signup.locator('#email').fill('selected-plan-acceptance@example.com')
        await signup.locator('#password').fill('test-only-long-password-123')
        await signup.locator('#confirmPassword').fill('test-only-long-password-123')
        await signup.get_by_text('Я принимаю',exact=False).click()
        await signup.get_by_role('button',name='Создать аккаунт').click()
        await signup.wait_for_url('**/subscription?plan=advanced',timeout=60000)
        await signup.get_by_text('Вы выбрали тариф',exact=False).wait_for(timeout=60000)
        subscription=await signup.evaluate("async () => {const r=await fetch('/api/users/me/subscription',{headers:{Authorization:'Bearer '+localStorage.getItem('access_token')}});return {status:r.status,body:await r.json()}}")
        assert subscription['status']==200 and subscription['body']['plan']=='trial',subscription
        assert not payment_posts,payment_posts
        await signup.screenshot(path=str(ROOT/'selected-plan.png'),full_page=True)
        report['selected_plan']={'redirect':'/subscription?plan=advanced','access_plan':subscription['body']['plan'],'payment_posts':len(payment_posts)}
        (ROOT/'browser-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print('BROWSER_PROFI_CHAIN_VERIFIED')
        await browser.close()
asyncio.run(main())
