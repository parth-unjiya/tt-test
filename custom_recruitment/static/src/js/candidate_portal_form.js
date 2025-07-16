/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";



publicWidget.registry.CandidatePortalForm = publicWidget.Widget.extend({
    selector: '.candidate_form',
    events: {
        'click .o_portal_form_submit': '_onFormSubmit',
        'click .linkedIn_form_submit': '_onlinkedInFormSubmit',
        'click .resume_form_submit': '_onResumeFormSubmit',
        
        'click #btadAdd': '_onAddAcademicRow',
        'click #btadRm': '_onRemoveAcademicRow',
        
        'click #addProfessional': '_onAddProfessionalRow',
        'click #removeProfessional': '_onRemoveProfessionalRow',
        
        // 'click #btAddFamily': '_onAddFamilyRow',
        // 'click #btRmFamily': '_onRemoveFamilyRow',
    },
    
    init() {
        this._super(...arguments);
    },

    start: async function () {
        await this._super(...arguments);

        const $tabButtons = $('button[data-bs-toggle="pill"]');
        const $tabContents = $('.tab-pane');

        let hash = window.location.hash;
        let $targetButton = $tabButtons.filter('[data-bs-target="' + hash + '"]');

        // Default to first tab if hash is missing or invalid
        if (!$targetButton.length) {
            $targetButton = $tabButtons.first();
            hash = $targetButton.data('bs-target');
        }

        // Function to manually switch tab
        function activateTab($btn) {
            $tabButtons.removeClass('active');
            $btn.addClass('active');

            const target = $btn.data('bs-target');
            $tabContents.removeClass('show active');
            $(target).addClass('show active');

            if (target) {
                history.replaceState(null, null, target);
            }
        }

        // Initial tab activation
        activateTab($targetButton);

        // On tab click
        $tabButtons.on('click', function () {
            activateTab($(this));
        });

        // Fade out any visible errors after 8 seconds
        ['#error', '#resume_error'].forEach(selector => {
            const $el = $(selector);
            if ($el.length && $el.is(':visible')) {
                setTimeout(() => $el.fadeOut(), 8000);
            }
        });
    },

    _onlinkedInFormSubmit: function (ev) {
        ev.preventDefault();

        const $form = $('#candidate_linkedin_form');
        const $urlInput = $('#linkedin_url');
        const url = $urlInput.val().trim();
        const $errorDiv = $('#linkedin_url_error');
        const $btn = $('.linkedIn_form_submit');

        $errorDiv.hide().text(''); // Reset previous error
        $('#linkedin_loader').hide();


        const linkedInPattern = /^https:\/\/(www\.)?linkedin\.com\/.*$/i;

        if (!url) {
            $errorDiv.text("Please enter your LinkedIn profile URL.").show();
            return;
        }

        if (!linkedInPattern.test(url)) {
            $errorDiv.text("Please enter a valid LinkedIn profile URL.").show();
            return;
        }

        const activeTab = $('button[data-bs-toggle="pill"].active').data('bsTarget');
        if (activeTab) {
            const currentAction = $form.attr('action') || window.location.pathname;
            const newAction = currentAction.split('#')[0] + activeTab;
            $form.attr('action', newAction);
        }

        $btn.prop('disabled', true);
        $('#linkedin_loader').show();
        $form[0].submit();
    },

    _onResumeFormSubmit: function (ev) {
        ev.preventDefault();
        const $form = $('#candidate_resume_form');
        const $fileInput = $('#resume_file');
        const $btn = $('.resume_form_submit');
        const file = $fileInput[0].files[0];
        const $errorDiv = $('#resume_file_error');

        $errorDiv.hide().text(''); // Reset error
        $('#resume_loader').hide();

        // Validation: file selected
        if (!file) {
            $errorDiv.text("Please select a resume file.").show();
            return;
        }

        // Validation: only PDF
        if (file.type !== "application/pdf") {
            $errorDiv.text("Only PDF files are accepted.").show();
            return;
        }

        const activeTab = $('button[data-bs-toggle="pill"].active').data('bsTarget');
        if (activeTab) {
            const currentAction = $form.attr('action') || window.location.pathname;
            const newAction = currentAction.split('#')[0] + activeTab;
            $form.attr('action', newAction);
        }

        // Proceed: show loader and disable button
        $btn.prop('disabled', true);
        $('#resume_loader').show();

        // Submit form
        $form[0].submit();
    },

    _onFormSubmit: async function (ev) {
        ev.preventDefault();

        // Clear all previous errors only once here
        this.$el.find('.form-error-msg').remove();
        this.$el.find('.is-invalid').removeClass('is-invalid');

        // Run all validations
        const personalValid = this._personalDetailsValidateFields();
        const academicValid = this._validateAcademicDetails();
        const professionalValid = this._validateProfessionalDetails();
        // const familyValid = this._validateFamilyDetails();


        // If any validation fails, stop submission
        if (!personalValid || !academicValid || !professionalValid) {
            console.log('Validation failed');
            return;
        }

        // // Serialize form data
        // const formData = this.$el.find('form').serializeArray();
        // const formattedData = {};
        // formData.forEach(field => {
        //     formattedData[field.name] = field.value;
        // });

        // Get Personal Details
        const personalDetails = {
            email_from: this.$el.find('#email').val(),
            partner_mobile: this.$el.find('#partner_mobile').val(),
            partner_phone: this.$el.find('#partner_phone').val(),
            dob: this.$el.find('#dob').val(),

            relevant_experience: this.$el.find('#relevant_experience').val(),
            total_experience: this.$el.find('#total_experience').val(),
            marital: this.$el.find('#marital_status').val(),
            linkedin_profile: this.$el.find('#linkedin_profile').val(),

            current_street: this.$el.find('#current_street').val(),
            current_street2: this.$el.find('#current_street2').val(),
            current_city: this.$el.find('#current_city').val(),
            current_zip: this.$el.find('#current_zip').val(),
            // current_state_id: this.$el.find('#current_state_id').val(),

            // permanent_street: this.$el.find('#permanent_street').val(),
            // permanent_street2: this.$el.find('#permanent_street2').val(),
            // permanent_city: this.$el.find('#permanent_city').val(),
            // permanent_zip: this.$el.find('#permanent_zip').val(),
            // permanent_state_id: this.$el.find('#permanent_state_id').val(),
   
        };

        // Get Academic Details as List of Dict
        const academicDetails = [];
        this.$el.find('.academic-entry').each(function () {
            academicDetails.push({
                degree: $(this).find('input[name^="degree_"]').val(),
                institute_name: $(this).find('input[name^="institute_name_"]').val(),
                passed_year: $(this).find('input[name^="passed_year_"]').val(),
                mark: $(this).find('input[name^="mark_"]').val(),
            });
        });

        // Get Professional Details as List of Dict
        const professionalDetails = [];
        this.$el.find('.professional-entry').each(function () {
            professionalDetails.push({
                company_name: $(this).find('input[name^="company_name_"]').val(),
                designation: $(this).find('input[name^="designation_"]').val(),
                start_date: $(this).find('input[name^="start_date_"]').val(),
                end_date: $(this).find('input[name^="end_date_"]').val(),
                reason: $(this).find('input[name^="reason_"]').val(),
                current_ctc: $(this).find('input[name^="current_ctc_"]').val(),
                expected_ctc: $(this).find('input[name^="expected_ctc_"]').val(),
                notice_period: $(this).find('input[name^="notice_period_"]').val(),
                last_appraisal_date: $(this).find('input[name^="last_appraisal_date_"]').val(),
            });
        });

        // Get Family Details as List of Dict
        // const familyDetails = [];
        // this.$el.find('.family-entry').each(function () {
        //     familyDetails.push({
        //         name: $(this).find('input[name^="family_name_"]').val(),
        //         relation: $(this).find('select[name^="relationship_"]').val(),
        //         occupation: $(this).find('input[name^="occupation_"]').val(),
        //     });
        // });

        // Final structured payload
        const finalPayload = {
            token: this.$el.find('#token').val(),
            personal: personalDetails,
            academic: academicDetails,
            professional: professionalDetails,
            // family: familyDetails,
        };

        console.log("Sending structured payload:", finalPayload);

        try {
            
            const response = await jsonrpc('/candidate/detail/submit', {
                data: finalPayload
            });



            console.log('Controller response:', response);

            if (response.success) {
                console.log('Form submitted successfully');
                window.location.href = '/candidate/evaluation/thankyou';
            }
            else if (response.error === 'Already Submitted') {
                window.location.href = '/candidate/evaluation/form/already-submitted';
            }
            else{
                console.error('Form submission failed:', response.error || 'Unknown error');
            }

        } catch (error) {
            console.error('Error submitting form:', error);
        }
        
    },

    // =================== Personal Details Section validation ====================
    _personalDetailsValidateFields: function () {
        let isValid = true;
        const self = this;

        function isNotBlank(value) {
            return value && value.trim() !== '';
        }

        // Define validations
        const validations = [
            {
                selector: '#email',
                required: true,
                validate: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
                message: 'Enter a valid email address',
            },
            {
                selector: '#partner_mobile',
                required: true,
                validate: (val) => /^\d{10}$/.test(val),
                message: 'Enter a valid 10-digit mobile number',
            },
            {
                selector: '#partner_phone',
                required: true,
                validate: (val) => /^\d{10}$/.test(val),
                message: 'Enter a valid 10-digit alernate number',
            },
            {
                selector: '#dob',
                required: true,
                validate: () => true,  // No format check, just required
                message: '',
            },
            {
                selector: '#relevant_experience',
                required: true,
                validate: () => true,
                message: 'Total relevant experience must be a non-negative number',
            },
            {
                selector: '#total_experience',
                required: true,
                validate: () => true,
                message: 'Total experience must be a non-negative number',
            },
            {
                selector: '#marital_status',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#linkedin_profile',
                required: true,
                validate: (val) => !val || val.startsWith('http'),
                message: 'LinkedIn profile must start with http/https',
            },
            {
                selector: '#current_street',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#current_street2',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#current_city',
                required: true,
                validate: () => true,
                message: '',
            },
            // {
            //     selector: '#current_state_id',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
            {
                selector: '#current_zip',
                required: true,
                validate: () => true,
                message: '',
            },
            // {
            //     selector: '#permanent_street',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
            // {
            //     selector: '#permanent_street2',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
            // {
            //     selector: '#permanent_city',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
            // {
            //     selector: '#permanent_state_id',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
            // {
            //     selector: '#permanent_zip',
            //     required: true,
            //     validate: () => true,
            //     message: '',
            // },
        ];

        validations.forEach(field => {
            const $input = self.$el.find(field.selector);
            const value = $input.val().trim();

            
            // Check if blank
            if (field.required && !isNotBlank(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                $input.after(`<div class="form-error-msg text-danger mt-1">This field is required</div>`);
                return;
            }
            
            // Check if value is present but invalid
            if (value && !field.validate(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                if (field.message) {
                    $input.after(`<div class="form-error-msg text-danger mt-1">${field.message}</div>`);
                }
            }
        });

        return isValid;
    },


    // ================== Academic Details Validation =====================
    _validateAcademicDetails: function () {
        let isValid = true;
        const self = this;

        function isNotBlank(value) {
            return value && value.trim() !== '';
        }

        const validations = [
            {
                selector: '#degree_1',
                required: true,
                validate: () => true, // Just required
                message: '',
            },
            {
                selector: '#institute_name_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#passed_year_1',
                required: true,
                validate: (val) => /^\d{4}$/.test(val),
                message: 'Enter a valid 4-digit year',
            },
            {
                selector: '#mark_1',
                required: true,
                validate: (val) => !isNaN(val) && parseFloat(val) >= 0 && parseFloat(val) <= 100,
                message: 'Enter a percentage between 0 and 100',
            },
        ];

        validations.forEach(field => {
            const $input = self.$el.find(field.selector);
            const value = $input.val().trim();

            if (field.required && !isNotBlank(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                $input.after(`<div class="form-error-msg text-danger mt-1">This field is required</div>`);
                return;
            }

            if (value && !field.validate(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                if (field.message) {
                    $input.after(`<div class="form-error-msg text-danger mt-1">${field.message}</div>`);
                }
            }
        });

        return isValid;
    },


    // ================== Professional Details Validation =====================
    _validateProfessionalDetails: function () {
        let isValid = true;
        const self = this;

        function isNotBlank(value) {
            return value && value.trim() !== '';
        }

        const validations = [
            {
                selector: '#company_name_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#designation_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#start_date_1',
                required: true,
                validate: (val) => /^\d{4}-\d{2}-\d{2}$/.test(val),
                message: 'Enter a valid start date',
            },
            {
                selector: '#end_date_1',
                required: true,
                validate: (val) => /^\d{4}-\d{2}-\d{2}$/.test(val),
                message: 'Enter a valid end date',
            },
            {
                selector: '#reason_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#current_ctc_1',
                required: true,
                validate: (val) => !isNaN(val) && parseFloat(val) >= 0,
                message: 'Enter a valid CTC amount',
            },
            {
                selector: '#expected_ctc_1',
                required: true,
                validate: (val) => !isNaN(val) && parseFloat(val) >= 0,
                message: 'Enter a valid expected CTC amount',
            },
            {
                selector: '#notice_period_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#last_appraisal_date_1',
                required: true,
                validate: (val) => /^\d{4}-\d{2}-\d{2}$/.test(val),
                message: 'Enter a valid date',
            },
        ];

        validations.forEach(field => {
            const $input = self.$el.find(field.selector);
            const value = $input.val().trim();

            if (field.required && !isNotBlank(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                $input.after(`<div class="form-error-msg text-danger mt-1">This field is required</div>`);
                return;
            }

            if (value && !field.validate(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                if (field.message) {
                    $input.after(`<div class="form-error-msg text-danger mt-1">${field.message}</div>`);
                }
            }
        });

        return isValid;
    },

    // ================== Family Details Validation =====================
    _validateFamilyDetails: function () {
        let isValid = true;
        const self = this;

        function isNotBlank(value) {
            return value && value.trim() !== '';
        }

        const validations = [
            {
                selector: '#family_name_1',
                required: true,
                validate: () => true,
                message: '',
            },
            {
                selector: '#relationship_1',
                required: true,
                validate: (val) => val !== '',
                message: 'Please select a relationship',
            },
            {
                selector: '#occupation_1',
                required: true,
                validate: () => true,
                message: '',
            },
        ];

        validations.forEach(field => {
            const $input = self.$el.find(field.selector);
            const value = $input.val().trim();

            if (field.required && !isNotBlank(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                $input.after(`<div class="form-error-msg text-danger mt-1">This field is required</div>`);
                return;
            }

            if (value && !field.validate(value)) {
                isValid = false;
                $input.addClass('is-invalid');
                if (field.message) {
                    $input.after(`<div class="form-error-msg text-danger mt-1">${field.message}</div>`);
                }
            }
        });

        return isValid;
    },


    // ======================= Academic Details ========================
    _onAddAcademicRow: function (ev) {
        ev.preventDefault();

        const $container = this.$el.find('#academic_container');
        const $lastRow = $container.find('.academic-entry').last();
        const $newRow = $lastRow.clone();

        // Get next index for new IDs/names
        const nextIndex = $container.find('.academic-entry').length + 1;

        // Clear values, error messages, and validation classes
        $newRow.find('input').each(function () {
            // const baseName = $(this).attr('name').split('_')[0];

            const nameAttr = $(this).attr('name') || '';
            const parts = nameAttr.split('_');
            const index = parts.pop();
            const baseName = parts.join('_');

            const newId = baseName + '_' + nextIndex;

            $(this).val(''); // Clear input value
            $(this).attr('name', newId);
            $(this).attr('id', newId);
            $(this).removeClass('is-invalid'); // Remove Bootstrap-style error class

            // Remove error message if exists
            const $error = $(this).siblings('.text-danger');
            if ($error.length) {
                $error.remove();
            }
        });

        $container.append($newRow);
    },

    _onRemoveAcademicRow: function (ev) {
        ev.preventDefault();
        const $container = this.$el.find('#academic_container');
        const $rows = $container.find('.academic-entry');
        if ($rows.length > 1) {
            $rows.last().remove();
        }
    },


    // ======================= Professional Details ========================
    _onAddProfessionalRow: function (ev) {
        ev.preventDefault();

        const $container = this.$el.find('#professional_container');
        const $lastRow = $container.find('.professional-entry').last();
        const $newRow = $lastRow.clone();

        // Change heading from "Current Company" to "Previous Company"
        $newRow.find('h5.text-muted.fw-semibold').text('Previous Company');

        // Get new index
        const nextIndex = $container.find('.professional-entry').length + 1;

        // Update cloned inputs
        $newRow.find('input').each(function () {
            // const name = $(this).attr('name').split('_')[0];

            const nameAttr = $(this).attr('name') || '';
            const parts = nameAttr.split('_');
            const index = parts.pop();
            const baseName = parts.join('_');

            const newId = baseName + '_' + nextIndex;

            $(this).val('');
            $(this).attr('id', newId);
            $(this).attr('name', newId);
            $(this).removeClass('is-invalid');

            // Remove validation messages
            $(this).siblings('.text-danger').remove();
        });

        $container.append($newRow);
    },

    _onRemoveProfessionalRow: function (ev) {
        ev.preventDefault();

        const $container = this.$el.find('#professional_container');
        const $rows = $container.find('.professional-entry');

        if ($rows.length > 1) {
            $rows.last().remove();
        }
    },


    // ======================= Family Details ========================
    _onAddFamilyRow: function (ev) {
        ev.preventDefault();

        const $container = this.$el.find('#family_container');
        const $lastRow = $container.find('.family-entry').last();
        const $newRow = $lastRow.clone();

        // Get next index
        const nextIndex = $container.find('.family-entry').length + 1;

        // Update inputs in new row
        $newRow.find('input, select').each(function () {
            // const baseName = $(this).attr('name')?.split('_')[0] || 'field';
            
            const nameAttr = $(this).attr('name') || '';
            const parts = nameAttr.split('_');
            const index = parts.pop();
            const baseName = parts.join('_');


            const newId = baseName + '_' + nextIndex;

            $(this).val('');
            $(this).attr('id', newId);
            $(this).attr('name', newId);
            $(this).removeClass('is-invalid');
            $(this).siblings('.form-error-msg').remove();
        });

        $container.append($newRow);
    },

    _onRemoveFamilyRow: function (ev) {
        ev.preventDefault();

        const $container = this.$el.find('#family_container');
        const $rows = $container.find('.family-entry');

        if ($rows.length > 1) {
            $rows.last().remove();
        }
    },

})