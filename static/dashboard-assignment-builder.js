(function (window, document, $) {
    'use strict';

    // #region debug-point A:reporter
    function debugReport(hypothesisId, location, msg, data) {
        fetch('http://127.0.0.1:7777/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: 'assignment-add-button',
                runId: 'pre-fix',
                hypothesisId: hypothesisId,
                location: location,
                msg: '[DEBUG] ' + msg,
                data: data || {},
                ts: Date.now()
            })
        }).catch(function () {});
    }
    // #endregion

    // #region debug-point B:script-bootstrap
    window.addEventListener('error', function (event) {
        debugReport('B', 'dashboard-assignment-builder.js:window.error', 'window error captured', {
            message: event.message,
            source: event.filename,
            line: event.lineno,
            column: event.colno
        });
    });
    debugReport('B', 'dashboard-assignment-builder.js:bootstrap', 'script bootstrap started', {
        hasJquery: !!$,
        readyState: document.readyState
    });
    // #endregion

    if (!$) {
        // #region debug-point C:no-jquery
        debugReport('C', 'dashboard-assignment-builder.js:no-jquery', 'jquery missing at bootstrap');
        // #endregion
        return;
    }

    function parseJsonScript(scriptId) {
        var script = document.getElementById(scriptId);
        if (!script) {
            return [];
        }
        try {
            return JSON.parse(script.textContent);
        } catch (error) {
            return [];
        }
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function hasSelect2($element) {
        return $element && typeof $element.select2 === 'function';
    }

    function AssignmentBuilder(root) {
        this.root = root;
        this.$root = $(root);
        this.$form = this.$root.closest('form');
        this.$cards = this.$root.find('[data-assignment-cards]');
        this.$empty = this.$root.find('[data-assignment-empty]');
        this.$generated = this.$root.find('[data-generated-inputs]');
        this.$addButton = this.$root.find('[data-add-assignment]');
        this.directory = parseJsonScript(this.$root.data('directoryScriptId'));
        this.initialAssignments = parseJsonScript(this.$root.data('initialScriptId'));
        this.addLabel = this.$root.data('addLabel') || 'إضافة أستاذ';
        this.cardIndex = 0;

        // #region debug-point D:constructor
        debugReport('D', 'dashboard-assignment-builder.js:constructor', 'builder constructed', {
            addButtonCount: this.$addButton.length,
            cardsCount: this.$cards.length,
            formCount: this.$form.length,
            directorySize: Array.isArray(this.directory) ? this.directory.length : -1,
            initialAssignmentsSize: Array.isArray(this.initialAssignments) ? this.initialAssignments.length : -1
        });
        // #endregion

        this.bindEvents();
        this.bootstrapCards();
    }

    AssignmentBuilder.prototype.bindEvents = function () {
        var self = this;

        this.$addButton.on('click', function (event) {
            event.preventDefault();
            // #region debug-point E:add-click
            debugReport('E', 'dashboard-assignment-builder.js:add-click', 'add button clicked', {
                existingCards: self.$cards.children().length
            });
            // #endregion
            try {
                self.addCard();
                // #region debug-point E:add-click-success
                debugReport('E', 'dashboard-assignment-builder.js:add-click-success', 'addCard completed', {
                    cardsAfter: self.$cards.children().length
                });
                // #endregion
            } catch (error) {
                // #region debug-point E:add-click-failure
                debugReport('E', 'dashboard-assignment-builder.js:add-click-failure', 'addCard threw error', {
                    message: error && error.message ? error.message : String(error)
                });
                // #endregion
                throw error;
            }
        });

        this.$cards.on('click', '[data-remove-card]', function () {
            var $card = $(this).closest('[data-assignment-card]');
            self.destroyCard($card);
            self.refreshTeacherOptions();
            self.toggleEmptyState();
        });

        this.$cards.on('change', '.js-assignment-teacher', function () {
            var $card = $(this).closest('[data-assignment-card]');
            self.populateStudentSelect($card, $(this).val(), []);
            self.refreshTeacherOptions();
        });

        this.$form.on('submit', function (event) {
            if (!self.serializeToHiddenInputs()) {
                event.preventDefault();
            }
        });
    };

    AssignmentBuilder.prototype.bootstrapCards = function () {
        var self = this;

        if (Array.isArray(this.initialAssignments) && this.initialAssignments.length) {
            this.initialAssignments.forEach(function (assignment) {
                self.addCard(assignment);
            });
        }

        this.refreshTeacherOptions();
        this.toggleEmptyState();
    };

    AssignmentBuilder.prototype.addCard = function (initialData) {
        // #region debug-point F:add-card-entry
        debugReport('F', 'dashboard-assignment-builder.js:addCard', 'addCard entered', {
            cardIndex: this.cardIndex,
            hasInitialData: !!initialData
        });
        // #endregion
        var cardId = 'assignment-card-' + this.cardIndex;
        var cardHtml = [
            '<div class="assignment-builder-card" data-assignment-card>',
            '  <div class="assignment-builder-card-head">',
            '    <div>',
            '      <h6 class="assignment-builder-title">بطاقة الأستاذ</h6>',
            '      <p class="assignment-builder-subtitle">اختر أستاذًا ثم حدّد الطلاب التابعين له.</p>',
            '    </div>',
            '    <button type="button" class="assignment-builder-remove" data-remove-card aria-label="حذف البطاقة">',
            '      <i class="bi bi-trash"></i>',
            '    </button>',
            '  </div>',
            '  <div class="assignment-builder-grid">',
            '    <div class="form-field">',
            '      <label class="field-label" for="' + cardId + '-teacher">الأستاذ</label>',
            '      <select class="form-control js-assignment-teacher" id="' + cardId + '-teacher" data-placeholder="ابحث عن أستاذ">',
            '        <option value=""></option>',
            '      </select>',
            '    </div>',
            '    <div class="form-field">',
            '      <label class="field-label" for="' + cardId + '-students">الطلاب المرتبطون</label>',
            '      <select class="form-control js-assignment-students" id="' + cardId + '-students" data-placeholder="اختر الطلاب" multiple></select>',
            '    </div>',
            '  </div>',
            '</div>'
        ].join('');

        var $card = $(cardHtml);
        this.$cards.append($card);

        this.initTeacherSelect($card, initialData ? String(initialData.teacher_id) : '');
        this.initStudentSelect($card);

        if (initialData && initialData.teacher_id) {
            this.populateStudentSelect($card, String(initialData.teacher_id), initialData.student_ids || []);
        } else {
            this.populateStudentSelect($card, '', []);
        }

        this.cardIndex += 1;
        this.toggleEmptyState();
        // #region debug-point F:add-card-exit
        debugReport('F', 'dashboard-assignment-builder.js:addCard', 'addCard exit', {
            cardIndex: this.cardIndex,
            cardsAfter: this.$cards.children().length
        });
        // #endregion
    };

    AssignmentBuilder.prototype.destroyCard = function ($card) {
        var $teacherSelect = $card.find('.js-assignment-teacher');
        var $studentSelect = $card.find('.js-assignment-students');

        if ($teacherSelect.data('select2')) {
            $teacherSelect.select2('destroy');
        }
        if ($studentSelect.data('select2')) {
            $studentSelect.select2('destroy');
        }
        $card.remove();
    };

    AssignmentBuilder.prototype.initTeacherSelect = function ($card, selectedTeacherId) {
        var $teacherSelect = $card.find('.js-assignment-teacher');
        this.populateTeacherSelect($teacherSelect, selectedTeacherId);
        this.initSelect2($teacherSelect, {
            placeholder: $teacherSelect.data('placeholder') || 'ابحث عن أستاذ',
            width: '100%',
            dir: 'rtl',
            allowClear: true
        });
        if (selectedTeacherId) {
            $teacherSelect.val(String(selectedTeacherId)).trigger('change.select2');
        }
    };

    AssignmentBuilder.prototype.initStudentSelect = function ($card) {
        var $studentSelect = $card.find('.js-assignment-students');
        this.initSelect2($studentSelect, {
            placeholder: $studentSelect.data('placeholder') || 'اختر الطلاب',
            width: '100%',
            dir: 'rtl',
            allowClear: false,
            closeOnSelect: false
        });
    };

    AssignmentBuilder.prototype.initSelect2 = function ($select, options) {
        if (!hasSelect2($select)) {
            return;
        }
        var $modal = this.$root.closest('.modal');
        if ($modal.length) {
            options.dropdownParent = $modal;
        }
        $select.select2(options);
    };

    AssignmentBuilder.prototype.refreshEnhancedSelect = function ($select) {
        if (hasSelect2($select) && $select.data('select2')) {
            $select.trigger('change.select2');
            return;
        }
        $select.trigger('change');
    };

    AssignmentBuilder.prototype.populateTeacherSelect = function ($teacherSelect, selectedTeacherId) {
        var selectedIds = this.getSelectedTeacherIds($teacherSelect);
        var options = ['<option value=""></option>'];

        this.directory.forEach(function (teacher) {
            var teacherId = String(teacher.id);
            var disabled = selectedIds.indexOf(teacherId) !== -1 && teacherId !== String(selectedTeacherId);
            var selected = teacherId === String(selectedTeacherId);
            options.push(
                '<option value="' + escapeHtml(teacherId) + '"' +
                (selected ? ' selected' : '') +
                (disabled ? ' disabled' : '') +
                '>' + escapeHtml(teacher.name) + '</option>'
            );
        });

        $teacherSelect.html(options.join(''));
    };

    AssignmentBuilder.prototype.populateStudentSelect = function ($card, teacherId, selectedStudentIds) {
        var $studentSelect = $card.find('.js-assignment-students');
        var teacher = this.findTeacherById(teacherId);
        var options = [];

        if (!teacher) {
            $studentSelect.prop('disabled', true).html('');
            $studentSelect.val(null);
            this.refreshEnhancedSelect($studentSelect);
            return;
        }

        (teacher.students || []).forEach(function (student) {
            var studentId = String(student.id);
            var selected = Array.isArray(selectedStudentIds) && selectedStudentIds.map(String).indexOf(studentId) !== -1;
            options.push(
                '<option value="' + escapeHtml(studentId) + '"' + (selected ? ' selected' : '') + '>' +
                escapeHtml(student.name) +
                '</option>'
            );
        });

        $studentSelect.prop('disabled', false).html(options.join(''));
        $studentSelect.val((selectedStudentIds || []).map(String));
        this.refreshEnhancedSelect($studentSelect);
    };

    AssignmentBuilder.prototype.findTeacherById = function (teacherId) {
        var normalized = String(teacherId || '');
        for (var i = 0; i < this.directory.length; i += 1) {
            if (String(this.directory[i].id) === normalized) {
                return this.directory[i];
            }
        }
        return null;
    };

    AssignmentBuilder.prototype.getSelectedTeacherIds = function (excludeSelect) {
        var ids = [];

        this.$cards.find('.js-assignment-teacher').each(function () {
            if (excludeSelect && this === excludeSelect[0]) {
                return;
            }
            if (this.value) {
                ids.push(String(this.value));
            }
        });

        return ids;
    };

    AssignmentBuilder.prototype.refreshTeacherOptions = function () {
        var self = this;

        this.$cards.find('.js-assignment-teacher').each(function () {
            var $teacherSelect = $(this);
            var currentValue = $teacherSelect.val();
            self.populateTeacherSelect($teacherSelect, currentValue);
            $teacherSelect.val(currentValue);
            self.refreshEnhancedSelect($teacherSelect);
        });
    };

    AssignmentBuilder.prototype.toggleEmptyState = function () {
        this.$empty.toggleClass('d-none', this.$cards.children().length > 0);
    };

    AssignmentBuilder.prototype.serializeToHiddenInputs = function () {
        var self = this;
        var hasError = false;
        var selectedTeacherIds = [];

        this.$generated.empty();

        this.$cards.find('[data-assignment-card]').each(function () {
            var $card = $(this);
            var teacherId = $card.find('.js-assignment-teacher').val();
            var studentIds = $card.find('.js-assignment-students').val() || [];

            if (!teacherId) {
                hasError = true;
                return false;
            }
            if (selectedTeacherIds.indexOf(String(teacherId)) !== -1) {
                hasError = true;
                return false;
            }

            selectedTeacherIds.push(String(teacherId));
            self.$generated.append('<input type="hidden" name="teacher_ids" value="' + escapeHtml(teacherId) + '">');

            studentIds.forEach(function (studentId) {
                self.$generated.append(
                    '<input type="hidden" name="teacher_' + escapeHtml(teacherId) + '_student_ids" value="' + escapeHtml(studentId) + '">'
                );
            });
        });

        if (hasError) {
            window.alert('يرجى اختيار أستاذ مختلف لكل بطاقة قبل الحفظ.');
            return false;
        }

        return true;
    };

    function initAssignmentBuilders() {
        // #region debug-point G:init-builders
        debugReport('G', 'dashboard-assignment-builder.js:initAssignmentBuilders', 'initializing assignment builders', {
            builderCount: $('[data-assignment-builder]').length
        });
        // #endregion
        $('[data-assignment-builder]').each(function () {
            if (!$(this).data('assignmentBuilderInstance')) {
                try {
                    $(this).data('assignmentBuilderInstance', new AssignmentBuilder(this));
                } catch (error) {
                    // #region debug-point G:init-builder-error
                    debugReport('G', 'dashboard-assignment-builder.js:initAssignmentBuilders', 'builder init failed', {
                        message: error && error.message ? error.message : String(error)
                    });
                    // #endregion
                    throw error;
                }
            }
        });
    }

    $(document).ready(initAssignmentBuilders);
})(window, document, window.jQuery);
