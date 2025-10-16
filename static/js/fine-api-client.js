/**
 * Fine API Client
 * JavaScript client for interacting with the Fine REST API
 */

const FineApiClient = {
    /**
     * Get CSRF token from cookie
     */
    getCSRFToken: function() {
        const name = 'csrftoken=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookieArray = decodedCookie.split(';');
        
        for (let i = 0; i < cookieArray.length; i++) {
            let cookie = cookieArray[i].trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return null;
    },
    
    /**
     * Make API request with proper headers
     */
    request: async function(url, method = 'GET', data = null) {
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
        };
        
        const options = {
            method,
            headers,
            credentials: 'same-origin'
        };
        
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API request failed');
            }
            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    },
    
    /**
     * Get all fines with optional filters
     */
    getFines: async function(filters = {}) {
        let url = '/fines/api/fines/';
        const queryParams = new URLSearchParams();
        
        // Add filters to query params
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                queryParams.append(key, filters[key]);
            }
        });
        
        if (queryParams.toString()) {
            url += '?' + queryParams.toString();
        }
        
        return await this.request(url);
    },
    
    /**
     * Get a single fine by ID
     */
    getFine: async function(fineId) {
        return await this.request(`/fines/api/fines/${fineId}/`);
    },
    
    /**
     * Waive a fine
     */
    waiveFine: async function(fineId, data) {
        return await this.request(`/fines/api/fines/${fineId}/waive/`, 'POST', data);
    },
    
    /**
     * Bulk waive fines
     */
    bulkWaiveFines: async function(data) {
        return await this.request('/fines/api/fines/bulk_waive/', 'POST', data);
    },
    
    /**
     * Get fine types
     */
    getFineTypes: async function() {
        return await this.request('/fines/api/fine-types/');
    },
    
    /**
     * Get fine students
     */
    getFineStudents: async function(fineId) {
        let url = '/fines/api/fine-students/';
        if (fineId) {
            url += `?fine=${fineId}`;
        }
        return await this.request(url);
    },
    
    /**
     * Mark a fine student as paid
     */
    markFineStudentPaid: async function(fineStudentId) {
        return await this.request(`/fines/api/fine-students/${fineStudentId}/mark_paid/`, 'POST');
    }
};