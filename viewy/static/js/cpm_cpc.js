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
  let pricingModelRadios = document.querySelectorAll('[name="pricing_model"]');
  let cpmContainer = document.getElementById('cpm-container');
  let cpcContainer = document.getElementById('cpc-container');

  // 今月のCPMをページから直接取得します
  let baseCPM = parseFloat(document.querySelector('.cpm').textContent.replace('今月のCPM: ', '').replace('円', ''));
  let baseCPC = parseFloat(document.querySelector('.cpc').textContent.replace('今月のCPC: ', '').replace('円', ''));

  // Get next month's CPC and CPM from the page, similar to current values
  let nextBaseCPM = parseFloat(document.querySelector('.next-cpm').textContent.replace('来月のCPM: ', '').replace('円', ''));
  let nextBaseCPC = parseFloat(document.querySelector('.next-cpc').textContent.replace('来月のCPC: ', '').replace('円', ''));

  function updateDisplay() {

    let startDateInput = document.querySelector('#start-date-input');
    let startDate = new Date(startDateInput.value);
    let currentDate = new Date();
    let isNextMonth = startDate.getMonth() === currentDate.getMonth() + 1 && startDate.getFullYear() === currentDate.getFullYear() ||
                      startDate.getMonth() === 0 && currentDate.getMonth() === 11 && startDate.getFullYear() === currentDate.getFullYear() + 1;

    // Choose the base CPC and CPM depending on the campaign's start date
    let baseCPMToUse = isNextMonth ? nextBaseCPM : baseCPM;
    let baseCPCToUse = isNextMonth ? nextBaseCPC : baseCPC;

    let selectedPricingModel = document.querySelector('[name="pricing_model"]:checked').value;

    if (selectedPricingModel === 'CPM') {
      let targetViews = parseInt(targetViewsInput.value);
      cpmContainer.style.display = 'block';
      cpcContainer.style.display = 'none';
      let adjustedCPM = calculateCPM(targetViews, baseCPMToUse);
      let budget = (targetViews / 1000) * adjustedCPM;

      // CPMと予算を表示する場所を指定してください
      document.querySelector('#calculated_cpm').textContent = adjustedCPM.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpm').textContent = budget.toLocaleString() + '円';
    } else {
      let targetClicks = parseInt(targetClicksInput.value);
      cpmContainer.style.display = 'none';
      cpcContainer.style.display = 'block';
      let adjustedCPC = calculateCPC(targetClicks, baseCPCToUse);
      let budget = targetClicks * adjustedCPC;

      // CPCを表示する場所を指定してください
      document.querySelector('#calculated_cpc').textContent = adjustedCPC.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpc').textContent = budget.toLocaleString() + '円';
    }
  }

  let startDateInput = document.querySelector('#start-date-input');
  startDateInput.addEventListener('change', updateDisplay);

  targetViewsInput.addEventListener('input', updateDisplay);
  targetClicksInput.addEventListener('input', updateDisplay);

  pricingModelRadios.forEach(radio => {
    radio.addEventListener('change', updateDisplay);
  });

  // 初期表示の更新
  updateDisplay();
});