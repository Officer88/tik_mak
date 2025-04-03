@admin_bp.route('/sliders/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_slide():
    form = SlideForm()
    
    if form.validate_on_submit():
        slide = Slide(
            title=form.title.data,
            subtitle=form.subtitle.data,
            image_url=form.image_url.data,
            button_text=form.button_text.data,
            button_url=form.button_url.data,
            order=form.order.data or 0,
            is_active=form.is_active.data
        )
        
        # Обработка загруженного изображения
        if form.image.data:
            # Используем новую функцию для сохранения изображений
            from image_utils import save_image
            
            # Сохраняем изображение через новую функцию
            saved_path = save_image(
                file_obj=form.image.data,
                folder_type='slides',
                max_size=(1200, 600)  # Размер слайдера
            )
            
            if saved_path:
                # Добавляем слеш впереди, если его нет
                if not saved_path.startswith('/'):
                    slide.image_url = '/' + saved_path
                else:
                    slide.image_url = saved_path
        
        db.session.add(slide)
        db.session.commit()
        
        flash('Слайд успешно добавлен', 'success')
        return redirect(url_for('admin.sliders'))
    
    return render_template('admin/sliders.html', form=form, add_mode=True)