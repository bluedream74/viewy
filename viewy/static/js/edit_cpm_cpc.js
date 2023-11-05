function calculateCPM(targetViews, baseCPM) {
  if (targetViews <= 50000) {
    return baseCPM;
  } else if (targetViews <= 100000) {
    return baseCPM - 50 * (targetViews - 50000) / 50000;
  } else if (targetViews <= 200000) {
    return (baseCPM - 50) - 50 * (targetViews - 100000) / 100000;
  } else {
    return baseCPM - 100;
  }
}

function calculateCPC(targetClicks, baseCPC) {
  if (targetClicks <= 500) {
    return baseCPC;
  } else if (targetClicks <= 1000) {
    return baseCPC - 5 * (targetClicks - 500) / 500;
  } else if (targetClicks <= 2000) {
    return (baseCPC - 5) - 5 * (targetClicks - 1000) / 1000;
  } else {
    return baseCPC - 10;
  }
}

document.addEventListener('DOMContentLoaded', function () {
  let targetViewsInput = document.querySelector('#id_target_views');
  let targetClicksInput = document.querySelector('#id_target_clicks');


  // 今月のCPMまたはCPCをページのspan要素から直接取得します
  let pricingModelElement = document.getElementById('pricing_model');
  let pricingModel = pricingModelElement.textContent.trim();
  let monthlyAdCostElement = document.getElementById('monthly_ad_cost');
  let monthlyAdCost = parseFloat(monthlyAdCostElement.textContent.replace('円', ''));

  let baseCPMToUse = pricingModel === 'CPM' ? monthlyAdCost : 0;
  let baseCPCToUse = pricingModel === 'CPC' ? monthlyAdCost : 0;

  function updateDisplay() {

    if (pricingModel === 'CPM') {
      if (targetViewsInput.value === '' || isNaN(targetViewsInput.value)) {
        document.querySelector('#calculated_cpm').textContent = '---';
        document.querySelector('#calculated_budget_cpm').textContent = '---';
        return; // 以降の処理を中断する
      }
      let targetViews = parseInt(targetViewsInput.value);
      let adjustedCPM = calculateCPM(targetViews, baseCPMToUse);
      let budget = (targetViews / 1000) * adjustedCPM;

      // CPMと予算を表示する場所を指定してください
      document.querySelector('#calculated_cpm').textContent = adjustedCPM.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpm').textContent = budget.toLocaleString() + '円';
    } else {
      if (targetClicksInput.value === '' || isNaN(targetClicksInput.value)) {
        document.querySelector('#calculated_cpc').textContent = '---';
        document.querySelector('#calculated_budget_cpc').textContent = '---';
        return; // 以降の処理を中断する
      }
      let targetClicks = parseInt(targetClicksInput.value);
      let adjustedCPC = calculateCPC(targetClicks, baseCPCToUse);
      let budget = targetClicks * adjustedCPC;

      // CPCを表示する場所を指定してください
      document.querySelector('#calculated_cpc').textContent = adjustedCPC.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpc').textContent = budget.toLocaleString() + '円';
    }
  }

  if (targetViewsInput) {
    targetViewsInput.addEventListener('input', function() {
      console.log('targetViewsInput changed'); // 確認用
      updateDisplay();
    });
  } else {
    console.log('targetViewsInput not found'); // エラー確認用
  }

  if (targetClicksInput) {
    targetClicksInput.addEventListener('input', function() {
      console.log('targetClicksInput changed'); // 確認用
      updateDisplay();
    });
  } else {
    console.log('targetClicksInput not found'); // エラー確認用
  }
  // 初期表示の更新
  updateDisplay();
});