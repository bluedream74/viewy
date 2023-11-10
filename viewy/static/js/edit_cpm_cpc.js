document.addEventListener('DOMContentLoaded', function () {
  let targetViewsInput = document.querySelector('#id_target_views');
  let targetClicksInput = document.querySelector('#id_target_clicks');


  // 今月のCPMまたはCPCをページのspan要素から直接取得します
  let pricingModelElement = document.getElementById('pricing-model');
  const pricingModel = pricingModelElement.textContent.trim();
  const actualCpcOrCpmElement = document.getElementById('actual-cpc-or-cpm');
  // 要素が存在する場合、そのテキスト内容を読み取る
  let actualCpcOrCpmValue;
  if (actualCpcOrCpmElement) {
    const textContent = actualCpcOrCpmElement.textContent.trim();
    // '円'を取り除き、数値に変換する
    actualCpcOrCpmValue = parseInt(textContent.replace('円', ''), 10);
  }

  function updateDisplay() {

    if (pricingModel === 'CPM') {
      if (targetViewsInput.value === '' || isNaN(targetViewsInput.value)) {
        document.querySelector('#calculated_cpm').textContent = '---';
        document.querySelector('#calculated_budget_cpm').textContent = '---';
        return; // 以降の処理を中断する
      }
      let targetViews = parseInt(targetViewsInput.value);
      let budget = (targetViews / 1000) * actualCpcOrCpmValue;

      // 見積金額を表示する場所を指定してください
      document.querySelector('#calculated_budget_cpm').textContent = budget.toLocaleString() + '円';
    } else {
      if (targetClicksInput.value === '' || isNaN(targetClicksInput.value)) {
        document.querySelector('#calculated_cpc').textContent = '---';
        document.querySelector('#calculated_budget_cpc').textContent = '---';
        return; // 以降の処理を中断する
      }
      let targetClicks = parseInt(targetClicksInput.value);
      let budget = targetClicks * actualCpcOrCpmValue;
      // 見積金額を表示する場所を指定してください
      document.querySelector('#calculated_budget_cpc').textContent = budget.toLocaleString() + '円';
    }
  }

  if (targetViewsInput) {
    targetViewsInput.addEventListener('input', function () {
      updateDisplay();
    });
  } else {
    console.log('targetViewsInput not found'); // エラー確認用
  }

  if (targetClicksInput) {
    targetClicksInput.addEventListener('input', function () {
      updateDisplay();
    });
  } else {
    console.log('targetClicksInput not found'); // エラー確認用
  }
  // 初期表示の更新
  updateDisplay();
});