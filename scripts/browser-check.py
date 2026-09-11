"""Exercise the adult and infant regional viewer, provenance and review tools in Chromium.

Set ATLAS_URL for a running preview and CHROMIUM_EXECUTABLE_PATH to use an
existing Chromium binary; otherwise Playwright uses its installed browser.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/browser'
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get('ATLAS_URL', 'http://127.0.0.1:3017')
errors, results = [], []

with sync_playwright() as p:
    executable = os.environ.get('CHROMIUM_EXECUTABLE_PATH')
    browser = p.chromium.launch(executable_path=executable, headless=True,
                               args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.add_init_script('''const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, options) {
      return original.call(this,type,type.startsWith('webgl')?{...options,preserveDrawingBuffer:true}:options);
    };''')

    def ready(count):
        page.wait_for_function("n=>document.querySelector('.identity-meta')?.textContent.includes(n)", arg=count)
        page.locator('.loading[role="status"]').wait_for(state='hidden', timeout=90000)
        assert page.locator('.loading.error').count() == 0

    def switch(label, count):
        page.get_by_label('Anatomical reference', exact=True).click()
        page.get_by_role('option', name=label, exact=True).click()
        ready(count)

    def search(query, label):
        page.get_by_role('button', name='Search anatomy', exact=True).click()
        page.get_by_label('Search named anatomical structures', exact=True).fill(query)
        page.get_by_role('option').filter(has_text=label).click()
        page.locator('.detail-sheet').wait_for()

    def shot(name):
        page.screenshot(path=str(OUT / (name + '.png')))

    def open_sources():
        page.get_by_role('button', name='Coverage & sources', exact=True).click()

    try:
        page.goto(BASE + '/?sex=female')
        ready('1,025 modeled pieces')
        canvas = page.locator('.scene canvas')
        pixel_stats = '''c=>{const s=document.createElement('canvas');s.width=c.width;s.height=c.height;
        const ctx=s.getContext('2d');ctx.drawImage(c,0,0);const a=ctx.getImageData(0,0,s.width,s.height).data;
        let colored=0,left=c.width,right=0,top=c.height,bottom=0;
        for(let i=0;i<a.length;i+=4){if(Math.max(a[i],a[i+1],a[i+2])-Math.min(a[i],a[i+1],a[i+2])>24){
          colored++;const x=(i/4)%c.width,y=Math.floor(i/4/c.width);
          left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}}
        return {colored,width:c.width,height:c.height,left,right,top,bottom};}'''
        page.wait_for_function(f"()=>({pixel_stats})(document.querySelector('.scene canvas')).colored>1000")
        stats = canvas.evaluate(pixel_stats)
        assert stats['colored'] > 1000, stats
        shot('female-desktop')
        before = canvas.screenshot()
        page.get_by_role('button', name='Rotate body', exact=True).click()
        page.wait_for_timeout(800)
        assert before != canvas.screenshot(), 'Rotation did not change canvas'
        page.get_by_role('button', name='Pause rotation', exact=True).click()
        search('uterus', 'body of uterus')
        if page.locator('.member-list button').count():
            page.locator('.member-list button').first.click()
        assert 'hra-female-assembly' in page.locator('.provenance').inner_text()
        with page.expect_download() as download:
            page.get_by_label('Download structure provenance', exact=True).click()
        assert download.value.suggested_filename.endswith('-provenance.json')
        page.get_by_role('button', name='Isolate structure', exact=True).click()
        page.wait_for_timeout(400)
        shot('female-provenance')
        page.get_by_role('button', name='Clear selection', exact=True).click()
        search('left radius', 'Left radius (partial CT reference)')
        assert 'MOOSE' in page.locator('.part-sources').inner_text()
        page.get_by_role('button', name='Isolate structure', exact=True).click()
        page.wait_for_timeout(400)
        shot('female-radius')
        page.get_by_role('button', name='Clear selection', exact=True).click()
        open_sources()
        assert '943 named concepts' in page.locator('.about-copy').inner_text()
        page.get_by_role('button', name='Review alignment', exact=True).click()
        page.locator('.registration-table tbody tr').first.wait_for()
        assert page.locator('.registration-table tbody tr').count() >= 6
        assert 'HRA viewer stage after transform' in page.locator('.registration-legend').inner_text()
        assert 'TCIA 003' not in page.locator('.registration-legend').inner_text()
        decisions = page.locator('.registration-table select')
        decisions.nth(0).select_option('confirmed')
        assert decisions.nth(1).input_value() == 'pending', 'Separate landmarks shared a decision'
        with page.expect_download() as review_download:
            page.get_by_role('button', name='Download review JSON').click()
        review = json.loads(Path(review_download.value.path()).read_text())
        assert len({item['id'] for item in review['landmarks']}) == len(review['landmarks'])
        assert sum(item['decision'] == 'confirmed' for item in review['landmarks']) == 1
        decisions.nth(0).select_option('pending')
        page.locator('.registration-toggle [role=switch]').click()
        page.wait_for_timeout(300)
        shot('female-registration')
        page.get_by_role('button', name='Close registration review').click()
        open_sources()
        page.get_by_role('button', name='Browse source catalog', exact=True).click()
        page.locator('.coverage-table tbody tr').first.wait_for()
        page.get_by_label('Coverage category').select_option('multi')
        assert page.locator('.coverage-table tbody tr').count() > 10
        page.get_by_label('Coverage category').select_option('segmented')
        page.get_by_label('Search coverage').fill('Skull')
        assert page.locator('.coverage-table tbody tr').count() > 0
        shot('source-catalog')
        page.get_by_role('button', name='Close coverage').click()
        page.get_by_label('Anatomical reference', exact=True).click()
        expect(page.get_by_role('option')).to_have_text(['Male', 'Female', 'Infant'])
        page.keyboard.press('Escape')
        switch('Male', '2,234 modeled pieces')
        switch('Infant', '94 modeled pieces')
        assert '91 pieces visible' in page.locator('.panel-foot').inner_text()
        page.wait_for_timeout(500)
        shot('infant-combined-desktop')
        search('hippocampus', 'Hippocampus left')
        assert 'dhcp-ga40-aggregate' in page.locator('.provenance').inner_text()
        page.get_by_role('button', name='Isolate structure', exact=True).click()
        page.wait_for_timeout(400)
        shot('infant-isolated')
        page.get_by_role('button', name='Clear selection', exact=True).click()
        search('heart', 'Heart')
        assert 'CUH-newborn-thorax-4916863' in page.locator('.provenance').inner_text()
        assert 'Tyndall' in page.locator('.part-sources').inner_text()
        with page.expect_download() as download:
            page.get_by_label('Download structure provenance', exact=True).click()
        provenance = json.loads(Path(download.value.path()).read_text())
        assert provenance['display_transform']['type'] == 'approximate display assembly'
        page.get_by_role('button', name='Isolate structure', exact=True).click()
        page.wait_for_timeout(400)
        shot('infant-heart')
        page.get_by_role('button', name='Clear selection', exact=True).click()
        page.get_by_role('button', name='All', exact=True).click()
        assert '94 pieces visible' in page.locator('.panel-foot').inner_text()
        page.get_by_role('button', name='Assemble and reset', exact=True).click()
        assert '91 pieces visible' in page.locator('.panel-foot').inner_text()
        open_sources()
        assert 'different sources' in page.locator('.about-copy').inner_text()
        page.keyboard.press('Escape')
        results.append({'desktop': 'three references, combined infant search, isolation, provenance, defaults and adult review', 'canvas': stats})
        print('Desktop model and review checks passed.', flush=True)
        combined_pixels = '''c=>{const s=document.createElement('canvas');s.width=c.width;s.height=c.height;
        const ctx=s.getContext('2d');ctx.drawImage(c,0,0);const a=ctx.getImageData(0,0,s.width,s.height).data;
        let brain=0,chest=0,brainY=0,chestY=0;
        for(let i=0;i<a.length;i+=4){const [r,g,b]=a.slice(i,i+3),y=Math.floor(i/4/s.width);
          if(r>g&&r-g<35&&g-b>30){brain++;brainY+=y;}
          if(r>b+6&&b>g+6){chest++;chestY+=y;}}
        return {brain,chest,brainY:brainY/brain,chestY:chestY/chest};}'''
        for width, height, query in [(390, 844, '?model=infant'), (320, 568, '?source=dhcp-neonatal'), (844, 390, '?model=infant-thorax')]:
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(BASE + '/' + query)
            ready('94 modeled pieces')
            assert page.get_by_label('Anatomical reference', exact=True).inner_text() == 'Infant'
            page.wait_for_function(f"()=>({pixel_stats})(document.querySelector('.scene canvas')).colored>1000")
            page.wait_for_timeout(500)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Horizontal overflow'
            combined = canvas.evaluate(combined_pixels)
            assert combined['brain'] > 100 and combined['chest'] > 100, combined
            assert combined['brainY'] < combined['chestY'], combined
            shot(f'{width}x{height}-infant-combined')
            search('trachea', 'Trachea')
            page.get_by_role('button', name='Isolate structure', exact=True).click()
            page.wait_for_timeout(400)
            shot(f'{width}x{height}-infant-trachea')
            page.get_by_role('button', name='Clear selection', exact=True).click()
            slider = page.get_by_role('slider')
            slider.focus()
            slider.press('End')
            page.wait_for_timeout(1200)
            shot(f'{width}x{height}-infant-combined-exploded')
            results.append({'viewport': [width, height], 'infant': 'brain above chest, trachea isolation and explosion', 'pixels': combined})
            print(f'Combined infant viewport {width}x{height} passed.', flush=True)
        assert not errors, errors
    except Exception as error:
        print(f'Browser check failed: {error}', flush=True)
        try:
            shot('failure')
        except Exception as screenshot_error:
            print(f'Failure screenshot unavailable: {screenshot_error}', flush=True)
        raise
    finally:
        browser.close()
(OUT / 'results.json').write_text(json.dumps({'checks': results, 'page_errors': errors}, indent=2) + '\n')
print('Browser checks passed; no JavaScript exceptions.')
