document.addEventListener('DOMContentLoaded', function () {
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfTokenElement) {
        console.error('CSRF token element not found');
        return;
    }
    const csrfToken = csrfTokenElement.value;
    
    let isLoading = false;

    // क्लासे लोड करने का लॉजिक
    document.getElementById('loadClassesBtn').addEventListener('click', function () {
        if (isLoading) return;
        isLoading = true;
        
        const button = this;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';

        fetch('/promotion/api/get-classes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.classes.length > 0) {
                renderSelectedClasses(data.classes);
                document.getElementById('selectedClassesContainer').classList.remove('hidden');
                document.getElementById('proceedToStudentsBtn').classList.remove('hidden');
            } else {
                alert('कोई क्लास नहीं मिली');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('त्रुटि हुई');
        })
        .finally(() => {
            isLoading = false;
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-download mr-2"></i>Load Classes';
        });
    });

    // छात्र लोड करने का लॉजिक
    document.getElementById('proceedToStudentsBtn').addEventListener('click', function () {
        if (isLoading) return;
        
        const selectedClasses = Array.from(
            document.querySelectorAll('input[name="selected_classes"]')
        ).map(input => input.value);

        if (selectedClasses.length === 0) {
            alert('कृपया कम से कम एक क्लास चुनें');
            return;
        }

        isLoading = true;
        const button = this;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';

        fetch('/promotion/api/load-students/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                class_ids: selectedClasses
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                renderStudents(data.students);
            } else {
                alert(data.message || 'छात्र लोड करने में त्रुटि');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('नेटवर्क त्रुटि हुई');
        })
        .finally(() => {
            isLoading = false;
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-users mr-2"></i>Load Students';
        });
    });

    // सहायक फंक्शन्स
    function renderSelectedClasses(classes) {
        const container = document.getElementById('selectedClassesList');
        container.innerHTML = '';

        classes.forEach(cls => {
            const div = document.createElement('div');
            div.className = 'bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center';
            div.innerHTML = `
                ${cls.full_name}
                <input type="hidden" name="selected_classes" value="${cls.id}">
                <button type="button" class="ml-2 text-blue-600 hover:text-blue-800 remove-class">
                    &times;
                </button>
            `;
            container.appendChild(div);
        });
    }

    function renderStudents(students) {
        const tbody = document.getElementById('studentsTbody');
        tbody.innerHTML = '';

        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4">कोई छात्र नहीं मिला</td></tr>';
            return;
        }

        // Fetch all classes first
        fetch('/promotion/api/get-all-classes/')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const allClasses = data.classes;
                    tbody.innerHTML = '';

                    students.forEach(student => {
                        const row = document.createElement('tr');
                        row.className = 'hover:bg-gray-50';
                        row.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap">
                            <input type="checkbox" class="h-4 w-4 text-blue-600 rounded student-check" value="${student.id}">
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">${student.adm_no}</td>
                        <td class="px-6 py-4 whitespace-nowrap">${student.name}</td>
                        <td class="px-6 py-4 whitespace-nowrap">${student.father}</td>
                        <td class="px-6 py-4 whitespace-nowrap">${student.current_class} - ${student.section}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <select class="new-class-select border rounded p-1" id="new-class-${student.id}">
                                <option value="">--Select--</option>
                                ${allClasses.map(cls => `
                                    <option value="${cls.id}">${cls.full_name}</option>
                                `).join('')}
                            </select>
                        </td>
                    `;
                        tbody.appendChild(row);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-red-500">Error loading data</td></tr>';
            });
    }

    // इवेंट डीलिगेशन फॉर रिमूव क्लास बटन
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-class')) {
            e.target.closest('div').remove();
            if (document.querySelectorAll('input[name="selected_classes"]').length === 0) {
                document.getElementById('selectedClassesContainer').classList.add('hidden');
                document.getElementById('proceedToStudentsBtn').classList.add('hidden');
            }
        }

        if (e.target.classList.contains('select-all')) {
            document.querySelectorAll('.student-check').forEach(checkbox => {
                checkbox.checked = e.target.checked;
            });
        }
    });

    // प्रमोट/ड्राफ्ट सेव करने का नया कोड
    const promoteForm = document.getElementById('attendanceForm');
    if (promoteForm) {
        promoteForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // 1. डेटा इकट्ठा करें
            const formData = new FormData(promoteForm);
            const selectedStudents = [];
            const newClasses = [];

            document.querySelectorAll('.student-check:checked').forEach(checkbox => {
                selectedStudents.push(checkbox.value);
                const newClassSelect = document.getElementById(`new-class-${checkbox.value}`);
                newClasses.push(newClassSelect.value);
            });

            // 2. वैलिडेशन
            if (selectedStudents.length === 0) {
                alert('कृपया कम से कम एक छात्र चुनें');
                return;
            }

            // 3. एक्शन निर्धारित करें
            const isPromote = e.submitter && e.submitter.name === 'promote';
            const action = isPromote ? 'promote' : 'save_draft';

            // अतिरिक्त वैलिडेशन अगर प्रमोट किया जा रहा है
            if (isPromote) {
                const allNewClassesSelected = newClasses.every(cls => cls !== '');
                if (!allNewClassesSelected) {
                    alert('कृपया सभी चयनित छात्रों के लिए नई क्लास चुनें!');
                    return;
                }
            }

            // 4. AJAX रिक्वेस्ट
            fetch('/promotion/promote-students/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    selected_students: selectedStudents,
                    new_class: newClasses,
                    [action]: true
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    if (isPromote) {
                        // पेज रिफ्रेश सिर्फ प्रमोट करने पर
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } else {
                    throw new Error(data.message || 'अज्ञात त्रुटि');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('त्रुटि: ' + error.message);
            });
        });
    }
});