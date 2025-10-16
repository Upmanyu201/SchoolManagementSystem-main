document.addEventListener("DOMContentLoaded", function () {
    const feeGroupSelect = document.getElementById("fee_group");
    const groupTypeSelect = document.getElementById("group_type");
    const feeTypeSelect = document.getElementById("fee_type");

    // Fee Group का चुनाव होने पर Group Type लोड करें
    feeGroupSelect.addEventListener("change", function () {
        const groupId = this.value;

        // Group Type लोड करना शुरू करें
        groupTypeSelect.innerHTML = '<option value="">Loading...</option>';

        fetch(`/fees/ajax/load-group-types/?fee_group_id=${groupId}`)
            .then(response => response.json())
            .then(data => {
                groupTypeSelect.innerHTML = '<option value="">-- Select Group Type --</option>';
                data.group_types.forEach(item => {
                    const opt = document.createElement("option");
                    opt.value = item.id;
                    opt.text = item.name;
                    groupTypeSelect.appendChild(opt);
                });

                // Group Type लोड होते ही Fee Type लोड करें
                feeTypeSelect.innerHTML = '<option value="">Loading...</option>';
                fetch(`/fees/ajax/load-fee-types/?group_type_id=${data.group_types[0].id}`)
                    .then(response => response.json())
                    .then(data => {
                        feeTypeSelect.innerHTML = '<option value="">-- Select Fee Type --</option>';
                        data.fee_types.forEach(item => {
                            const opt = document.createElement("option");
                            opt.value = item.id;
                            opt.text = item.name;
                            feeTypeSelect.appendChild(opt);
                        });
                    });
            });
    });

    // Group Type का चुनाव होने पर Fee Type लोड करें
    groupTypeSelect.addEventListener("change", function () {
        const groupTypeName = this.value;
        feeTypeSelect.innerHTML = '<option value="">Loading...</option>';
        fetch(`/fees/ajax/load-fee-types/?group_type_name=${groupTypeName}`)
            .then(response => response.json())
            .then(data => {
                feeTypeSelect.innerHTML = '<option value="">-- Select Fee Type --</option>';
                data.fee_types.forEach(item => {
                    const opt = document.createElement("option");
                    opt.value = item.id;
                    opt.text = item.name;
                    feeTypeSelect.appendChild(opt);
                });
            });
    });
});

