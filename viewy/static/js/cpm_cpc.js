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

function calculateCPC(targetViews, baseCPC) {
  if (targetViews <= 50000) {
    return baseCPC;
  } else if (targetViews <= 100000) {
    return baseCPC - 5 * (targetViews - 50000) / 50000;
  } else if (targetViews <= 200000) {
    return (baseCPC - 5) - 5 * (targetViews - 100000) / 100000;
  } else {
    return baseCPC - 10;
  }
}

document.addEventListener('DOMContentLoaded', function () {
  let targetViewsInput = document.querySelector('#target_views input');
  let pricingModelRadios = document.querySelectorAll('[name="pricing_model"]');
  let cpmContainer = document.getElementById('cpm-container');
  let cpcContainer = document.getElementById('cpc-container');

  let budgetInput = document.getElementById('budget_input');
  
  // 今月のCPMをページから直接取得します
  let baseCPM = parseFloat(document.querySelector('.cpm').textContent.replace('今月のCPM: ', '').replace('円', ''));
  let baseCPC = parseFloat(document.querySelector('.cpc').textContent.replace('今月のCPC: ', '').replace('円', ''));

  function updateDisplay() {
    let targetViews = parseInt(targetViewsInput.value);
    let selectedPricingModel = document.querySelector('[name="pricing_model"]:checked').value;
    
    if (selectedPricingModel === 'CPM') {
      cpmContainer.style.display = 'block';
      cpcContainer.style.display = 'none';
      budgetInput.removeAttribute('required'); // CPMの場合、予算入力を必須から削除
      let adjustedCPM = calculateCPM(targetViews, baseCPM);
      let budget = (targetViews / 1000) * adjustedCPM;
      
      // CPMと予算を表示する場所を指定してください
      document.querySelector('#calculated_cpm').textContent = adjustedCPM.toLocaleString() + '円';
      document.querySelector('#calculated_budget').textContent = budget.toLocaleString() + '円';
    } else {
      cpmContainer.style.display = 'none';
      cpcContainer.style.display = 'block';
      budgetInput.setAttribute('required', true); // CPCの場合、予算入力を必須に設定
      let adjustedCPC = calculateCPC(targetViews, baseCPC);
      
      // CPCを表示する場所を指定してください
      document.querySelector('#calculated_cpc').textContent = adjustedCPC.toLocaleString() + '円';
    }
  }

  targetViewsInput.addEventListener('input', updateDisplay);

  pricingModelRadios.forEach(radio => {
    radio.addEventListener('change', updateDisplay);
  });

  // 初期表示の更新
  updateDisplay();
});